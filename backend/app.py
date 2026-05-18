"""
GemmaCart – Home Depot In-Store Product Finder & Navigator
FastAPI backend powered by Gemma 4 (via Ollama) + SerpAPI (live HD product data).

Endpoints:
  GET  /api/store/meta       – Store info + Google Maps link
  GET  /api/store/layout     – Grid sections + entrance/exit (for map render)
  GET  /api/store/products   – Offline product catalogue
  POST /api/search/text      – Natural-language product search (Gemma 4 + SerpAPI)
  POST /api/search/image     – Upload photo → identify + locate products
  POST /api/route/plan       – Optimise multi-item shopping route
  GET  /api/model/status     – Which Gemma model is active
  GET  /api/serpapi/status   – SerpAPI quota info
"""

import sys
import os
import re
import asyncio

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import httpx

import hd_store_data as hd
import hd_gemma_client as gc
from serpapi_client import get_serpapi_status, locate_store_by_zip, get_current_store, set_current_store

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GemmaCart – Home Depot Navigator",
    description="AI-powered in-store product finder for The Home Depot using Gemma 4 + SerpAPI",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class TextSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    history: list[HistoryMessage] = Field(default_factory=list, max_items=10)

class RouteRequest(BaseModel):
    product_ids: list[str] = Field(..., min_items=1, max_items=30)


# ── HTML frontend ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"status": "GemmaCart HD API running", "docs": "/docs"}


# ── Store info endpoints ──────────────────────────────────────────────────────

@app.get("/api/store/meta")
async def store_meta():
    # Return the live store context (may have been updated by ZIP search)
    return get_current_store()


@app.get("/api/store/locate")
async def locate_store(zip: str):
    """
    Find the nearest Home Depot for a given ZIP code and update the active store.
    The found store becomes the context for all subsequent product searches.
    """
    if not zip or len(zip) < 4:
        raise HTTPException(400, detail="Provide a valid ZIP code")

    result = await locate_store_by_zip(zip)
    if "error" in result:
        raise HTTPException(404, detail=result["error"])

    # Update global store context so searches use the new store
    set_current_store(result)
    return result


@app.get("/api/store/layout")
async def store_layout():
    return {
        "grid": hd.GRID,
        "sections": hd.SECTIONS,
        "entrance": hd.ENTRANCE,
        "exit": hd.EXIT,
    }


@app.get("/api/store/products")
async def all_products(section: str | None = None):
    products = hd.FALLBACK_PRODUCTS
    if section:
        products = [p for p in products if p["section"] == section]
    return {"count": len(products), "products": products}


# ── AI search endpoints ───────────────────────────────────────────────────────

@app.post("/api/search/text")
async def text_search(req: TextSearchRequest):
    """
    Natural-language product search: Gemma 4 function calling → SerpAPI (live HD data).
    Falls back to offline keyword search if Ollama is unreachable.
    """
    history = [{"role": m.role, "content": m.content} for m in req.history]
    try:
        result = await gc.chat_with_tools(req.query, history=history)
        # Auto-plan route if multiple products were found
        if result["products"] and not result["route"] and len(result["products"]) > 1:
            ids = [p["id"] for p in result["products"][:10]]
            result["route"] = hd.plan_route(ids, result["products"])
        return result
    except httpx.ConnectError:
        result = await gc.local_search(req.query)
        result["warning"] = "Ollama offline – using keyword search. Start Ollama for full AI + live data."
        return result
    except Exception as exc:
        result = await gc.local_search(req.query)
        result["warning"] = f"Gemma unavailable ({type(exc).__name__}) – using keyword search."
        return result


_IMG_STOPWORDS = {
    "the","and","for","are","with","this","that","from","have","also","some",
    "can","you","your","they","been","will","use","used","using","its","image",
    "shows","show","visible","appears","appear","photo","picture","product",
    "item","just","only","very","home","depot","store","hardware",
}

@app.post("/api/search/image")
async def image_search(
    file: UploadFile = File(...),
    hint: str = Form(default=""),
):
    """
    Multimodal image search — tool-calling first pipeline:
      1. chat_with_image: Gemma 4 sees the image AND calls search_products() directly.
         This is the most accurate path — Gemma picks the search term, not us.
      2. Fallback: describe_image → local keyword search if tool-calling finds nothing.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="File must be an image (jpeg, png, webp)")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, detail="Image too large (max 10 MB)")

    mime = file.content_type or "image/jpeg"

    _FILLER = re.compile(
        r"^\s*(find|get|show|search|look\s*for|where\s*is|where\s*are|i\s+need|"
        r"i\s+want|looking\s+for|need\s+to\s+find|help\s+me\s+find)\s+(a|an|the|some)?\s*",
        re.IGNORECASE,
    )
    _SKIP = _IMG_STOPWORDS | {"find","get","show","search","need","want","help","please"}
    clean_hint = _FILLER.sub("", hint.strip()).strip()

    # ── Launch vision tasks in parallel ──────────────────────────────────────
    # describe_image runs concurrently with chat_with_image so we always have
    # a product description ready without extra latency.
    hint_task = None
    if clean_hint:
        hint_task = asyncio.create_task(
            asyncio.to_thread(hd.search_fallback, clean_hint, 6)
        )
    # Start describe_image immediately — it's our most reliable vision path
    describe_task = asyncio.create_task(gc.describe_image(image_bytes, mime, hint))

    gemma_description = ""
    try:
        full_result = await gc.chat_with_image(image_bytes, mime, hint)

        if full_result.get("products"):
            # Gemma found products via tool-calling — use them directly
            if hint_task:
                hint_task.cancel()
            describe_task.cancel()
            products = full_result["products"]
            route = full_result.get("route", {})
            if not route and len(products) > 1:
                route = hd.plan_route([p["id"] for p in products[:10]], products)
            return {
                "model": full_result.get("model", "gemma4"),
                "reply": full_result.get("reply", f"I found {len(products)} product(s):"),
                "products": products,
                "route": route,
                "source": full_result.get("source", "gemma4"),
                "similar": False,
                "image_query": full_result.get("reply", ""),
            }

        # Tool-calling ran but found no products — use Gemma's text reply if available.
        # Discard it if Gemma is saying it can't see the image (refusal phrases).
        _reply = full_result.get("reply", "")
        _refusal = any(p in _reply.lower() for p in (
            "image didn't", "image did not", "can't see", "cannot see",
            "no image", "please upload", "please provide", "please share",
            "no product", "i don't see", "i cannot identify",
        ))
        gemma_description = "" if _refusal else _reply

    except httpx.ConnectError:
        if hint_task:
            hint_task.cancel()
        describe_task.cancel()
        return {
            "model": "offline",
            "reply": "Ollama not running. Start Ollama to enable vision search.",
            "products": [], "route": {}, "source": "offline",
            "image_query": "", "similar": False,
        }
    except Exception:
        pass  # fall through to describe_image result below

    # If chat_with_image gave no description, wait for describe_image result
    # (it was already running in parallel, so latency cost is minimal)
    if not gemma_description:
        try:
            gemma_description = await describe_task
        except Exception:
            gemma_description = ""
    else:
        describe_task.cancel()

    # ── Fallback: keyword search using Gemma's text description ──────────────
    clean_desc   = _FILLER.sub("", gemma_description).strip()
    search_query = clean_desc or clean_hint or gemma_description or hint.strip()

    if not search_query:
        if hint_task:
            hint_task.cancel()
        return {
            "model": "gemma4",
            "reply": "I couldn't identify any product in that image. Try adding a text description.",
            "products": [], "route": {}, "source": "vision_fail",
            "image_query": "", "similar": False,
        }

    noun_tokens = [w for w in re.findall(r"[a-zA-Z0-9]{2,}", search_query.lower()) if w not in _SKIP]
    noun_phrase = " ".join(noun_tokens[:4])

    products: list[dict] = []
    source = "local_fallback"
    is_similar = False

    if noun_phrase:
        products = hd.search_fallback(noun_phrase, max_results=6)
    if not products and search_query != noun_phrase:
        products = hd.search_fallback(search_query, max_results=6)
    if not products and hint_task:
        try:
            products = await hint_task
            hint_task = None
            is_similar = bool(products)
        except Exception:
            pass
    if not products:
        is_similar = True
        for kw in noun_tokens[:4]:
            if len(kw) >= 3:
                products = hd.search_fallback(kw, max_results=6)
                if products:
                    break
    if not products:
        is_similar = True
        try:
            live = await gc.chat_with_tools(noun_phrase or search_query)
            products = live.get("products", [])
            if products:
                source = live.get("source", "serpapi_live")
        except Exception:
            pass

    if hint_task and not hint_task.done():
        hint_task.cancel()

    for p in products:
        gc._session_products[p["id"]] = p

    route: dict = {}
    if len(products) > 1:
        route = hd.plan_route([p["id"] for p in products], products)

    if products and is_similar:
        reply = (
            f"I identified \"{gemma_description or hint}\" but couldn't find an exact match. "
            "Here are the closest products I found in the store:"
        )
    elif products:
        reply = f"I found {len(products)} product(s) matching \"{gemma_description or hint}\":"
    else:
        reply = (
            f"I identified \"{gemma_description or hint}\" but couldn't find matching products "
            "in the store catalogue. Try the 🔍 barcode scanner or a text search."
        )

    return {
        "model": "gemma4",
        "reply": reply,
        "products": products,
        "route": route,
        "source": source,
        "similar": is_similar,
        "image_query": gemma_description,
    }


@app.post("/api/route/plan")
async def plan_route(req: RouteRequest):
    """
    Compute optimised shopping route (nearest-neighbour TSP) for a list of product IDs.
    Accepts IDs from either the live SerpAPI results or the offline catalogue.
    """
    # Merge session products with fallback catalogue
    all_products = list(gc._session_products.values()) + hd.FALLBACK_PRODUCTS
    route = hd.plan_route(req.product_ids, all_products)
    if not route["steps"]:
        raise HTTPException(404, detail="None of the given product IDs were found")
    return route


# ── Status endpoints ──────────────────────────────────────────────────────────

@app.get("/api/model/status")
async def model_status():
    try:
        model = await gc.resolve_model()
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{gc.OLLAMA_URL}/api/tags")
            tags = [m["name"] for m in resp.json().get("models", [])]
        return {"status": "online", "active_model": model, "available_models": tags}
    except Exception as exc:
        return {"status": "offline", "active_model": None, "error": str(exc)}


@app.get("/api/serpapi/status")
async def serpapi_status():
    return await get_serpapi_status()


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
