"""
GemmaCart – Home Depot edition.
Gemma 4 with function calling backed by SerpAPI (live HD data) + hd_store_data fallback.
"""

from __future__ import annotations

import io
import json
import base64
import hashlib
import httpx
import asyncio
from typing import Any

import hd_store_data as hd
from serpapi_client import search_home_depot

# ── Image normalisation ───────────────────────────────────────────────────────

def _normalise_image(image_bytes: bytes, max_dim: int = 1024) -> tuple[bytes, str]:
    """
    Convert any uploaded image to a clean RGB PNG at most max_dim×max_dim pixels.
    Ollama's gemma4 handles PNG more reliably than JPEG for some encodings.
    Returns (png_bytes, "image/png").
    """
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), "image/png"
    except Exception:
        # If Pillow fails for any reason, return original unchanged
        return image_bytes, "image/jpeg"

# ── Ollama config ─────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434"
MODEL_PREFERENCE = ["gemma4:latest", "gemma4:31b", "gemma4:27b", "gemma4:4b", "gemma4:2b", "gemma2:2b", "gemma:7b"]

_resolved_model: str | None = None


async def resolve_model() -> str:
    global _resolved_model
    if _resolved_model:
        return _resolved_model
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            available = {m["name"] for m in resp.json().get("models", [])}
        for candidate in MODEL_PREFERENCE:
            if candidate in available:
                _resolved_model = candidate
                return _resolved_model
        _resolved_model = list(available)[0] if available else "gemma4:27b"
        return _resolved_model
    except Exception:
        _resolved_model = "gemma4:27b"
        return _resolved_model


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the Home Depot store for products matching a query. "
                "Returns real product names, prices, and aisle/bay location. "
                "Use this whenever the user asks about finding a product, checking availability, "
                "or wants to know where something is located in the store."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product name, brand, or description to search for",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default 6)",
                        "default": 6,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_shopping_route",
            "description": (
                "Plan an optimised shopping route through the Home Depot store for multiple products. "
                "Returns the order to visit each item to minimise walking distance, "
                "with step-by-step aisle directions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of product IDs to include in the route",
                    },
                },
                "required": ["product_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_section_info",
            "description": "Get information about a specific Home Depot department or section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_name": {
                        "type": "string",
                        "description": "Department or section name (e.g. 'tools', 'plumbing', 'electrical', 'lumber', 'paint')",
                    },
                },
                "required": ["section_name"],
            },
        },
    },
]


# ── Tool executor ─────────────────────────────────────────────────────────────

# Cache for live products returned this session (for route planning)
_session_products: dict[str, dict] = {}
_SESSION_MAX = 500  # cap to prevent unbounded memory growth

# Vision result cache — keyed by MD5(image_bytes + hint) to skip repeated Gemma calls
_vision_cache: dict[str, str] = {}
_VISION_CACHE_MAX = 30

async def execute_tool_async(name: str, args: dict) -> Any:
    if name == "search_products":
        query = args.get("query", "")
        max_results = args.get("max_results", 6)
        products, source = await search_home_depot(query, max_results)
        # Cache for route planning; evict oldest entries when cap reached
        if len(_session_products) >= _SESSION_MAX:
            evict = list(_session_products.keys())[:max_results]
            for k in evict:
                _session_products.pop(k, None)
        for p in products:
            _session_products[p["id"]] = p
        return {"products": products, "source": source, "count": len(products)}

    elif name == "plan_shopping_route":
        pids = args.get("product_ids", [])
        # Pass session products so live results are used
        route = hd.plan_route(pids, list(_session_products.values()))
        return route

    elif name == "get_section_info":
        sname = args.get("section_name", "").lower().replace(" ", "_")
        sec = hd.SECTION_MAP.get(sname)
        if not sec:
            # Try partial match
            for sid, sdata in hd.SECTION_MAP.items():
                if sname in sid or sname in sdata["label"].lower():
                    sec = sdata
                    break
        if sec:
            return {
                "section": sec["id"],
                "label": sec["label"],
                "grid_position": f"Row {sec['gy']+1}, Column {sec['gx']+1}",
                "store_area": "Back of store" if sec["gy"] < 3 else ("Middle" if sec["gy"] < 7 else "Front"),
            }
        return {"error": f"Section '{sname}' not found. Available: " + ", ".join(hd.SECTION_MAP.keys())}

    return {"error": f"Unknown tool: {name}"}


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are GemmaCart, an AI shopping assistant for The Home Depot.
Your job is to help shoppers find products quickly and navigate the store efficiently.

Store layout: Lumber/Building Materials at the back. Tools, Electrical, Plumbing in the middle.
Paint, Hardware, Lighting toward the front-right. Garden and Appliances near the front.

STRICT RULES — follow every time:
1. ALWAYS call search_products immediately. Never answer a product question without searching first.
2. If the user mentions multiple product types (e.g. "pipes and fittings"), call search_products
   ONCE for each type — do NOT ask the user if they want you to search. Just search all of them.
3. NEVER ask follow-up questions like "would you like me to search for X?". Search proactively.
4. After receiving tool results, give a concise answer with product name, price, and aisle.
5. Keep responses brief — shoppers are on their feet.
6. Do NOT make up aisle numbers or locations. Only use data from tool results.
7. If a product is not found, suggest the closest alternative.
"""


# ── Agentic chat loop ─────────────────────────────────────────────────────────

async def chat_with_tools(user_message: str, history: list[dict] | None = None) -> dict:
    """
    Send a text query to Gemma 4 with HD function-calling enabled.
    history: list of {"role": "user"|"assistant", "content": str} for conversation context.
    Returns { reply, products, route, source }
    """
    model = await resolve_model()
    # Prepend conversation history (last 6 turns max) so Gemma remembers context
    prior = (history or [])[-6:]
    messages = prior + [{"role": "user", "content": user_message}]

    found_products: list[dict] = []
    route_data: dict = {}
    final_reply = ""
    data_source = "gemma4"

    async with httpx.AsyncClient(timeout=120) as client:
        for _ in range(6):
            payload = {
                "model": model,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "tools": TOOLS,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 1024},
            }
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

            msg = data.get("message", {})
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                final_reply = msg.get("content", "")
                break

            messages.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args = tc["function"].get("arguments", {})
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                result = await execute_tool_async(fn_name, fn_args)

                if fn_name == "search_products" and isinstance(result, dict):
                    for p in result.get("products", []):
                        if p not in found_products:
                            found_products.append(p)
                    data_source = result.get("source", data_source)
                elif fn_name == "plan_shopping_route" and isinstance(result, dict):
                    route_data = result

                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                })

    return {
        "model": model,
        "reply": final_reply,
        "products": found_products,
        "route": route_data,
        "source": data_source,
    }


async def chat_with_image(image_bytes: bytes, mime_type: str = "image/jpeg", hint: str = "") -> dict:
    """
    Send an image to Gemma 4 vision. Gemma identifies the product(s), then searches HD.
    """
    # Normalise to PNG to avoid JPEG encoding issues with Ollama
    image_bytes, mime_type = _normalise_image(image_bytes)
    model = await resolve_model()
    b64 = base64.b64encode(image_bytes).decode()

    vision_prompt = (
        f"{hint}\n\n" if hint else ""
    ) + (
        "Look at this image carefully. Identify any hardware, home improvement, or building products, "
        "tool brands, product labels, or shopping list items visible. "
        "List each item clearly, then search for them in the Home Depot store."
    )

    messages = [{
        "role": "user",
        "content": vision_prompt,
        "images": [b64],
    }]

    found_products: list[dict] = []
    route_data: dict = {}
    final_reply = ""
    last_content = ""   # captures any text Gemma emits during tool-call loop
    data_source = "gemma4"

    async with httpx.AsyncClient(timeout=120) as client:
        for _ in range(6):
            payload = {
                "model": model,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "tools": TOOLS,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 1024},
            }
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

            msg = data.get("message", {})
            if msg.get("content"):
                last_content = msg["content"]
            tool_calls = msg.get("tool_calls", [])

            if not tool_calls:
                final_reply = msg.get("content", "")
                break

            messages.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args = tc["function"].get("arguments", {})
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                result = await execute_tool_async(fn_name, fn_args)

                if fn_name == "search_products" and isinstance(result, dict):
                    for p in result.get("products", []):
                        if p not in found_products:
                            found_products.append(p)
                    data_source = result.get("source", data_source)
                elif fn_name == "plan_shopping_route" and isinstance(result, dict):
                    route_data = result

                messages.append({
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False),
                })
        else:
            # Loop exhausted without a tool-free response — use last captured text
            final_reply = last_content

    return {
        "model": model,
        "reply": final_reply,
        "products": found_products,
        "route": route_data,
        "source": data_source,
    }


async def describe_image(image_bytes: bytes, mime_type: str = "image/jpeg", hint: str = "") -> str:
    """
    Ask Gemma 4 vision to identify any home-improvement product in an image.

    Tries three progressively simpler approaches so real product images always
    get a usable search term:
      1. /api/chat  — full structured prompt (text-first + visual rules)
      2. /api/generate — same prompt via the generate endpoint (more reliable
                         for some image types)
      3. /api/chat  — minimal prompt: "Name the product in this image."

    Returns a product search query string — empty string only if all three fail.
    """
    # Normalise to PNG — avoids JPEG encoding issues in Ollama
    image_bytes, _ = _normalise_image(image_bytes)

    # Cache check — avoid calling Gemma for the same image+hint combo
    cache_key = hashlib.md5(image_bytes + hint.encode()).hexdigest()
    if cache_key in _vision_cache:
        return _vision_cache[cache_key]

    model = await resolve_model()
    b64 = base64.b64encode(image_bytes).decode()
    hint_line = f"Hint: \"{hint}\". " if hint else ""

    FULL_PROMPT = (
        f"{hint_line}"
        "Identify the home improvement product in this image.\n\n"
        "Rule 1 — READ TEXT FIRST: look for any readable text on the product, packaging, "
        "label, or screen (brand name, model number, category). "
        "Use that exact text — it is always more accurate than guessing visually.\n\n"
        "Rule 2 — VISUAL (only if no text): identify the product type carefully.\n"
        "Power tools — by shape:\n"
        "  • Angle grinder — disc perpendicular to body, no base plate\n"
        "  • Circular saw — toothed blade parallel to body, flat base plate\n"
        "  • Jigsaw — thin vertical blade at bottom\n"
        "  • Drill/driver — chuck at front, cylindrical body\n"
        "  • Reciprocating saw — long blade extending forward\n"
        "Painting: paint roller, paint brush, paint tray, paint can.\n"
        "Pipes: specify PVC / copper / steel and DWV / supply / conduit.\n\n"
        "Reply with ONLY the product name in 3-7 words. If totally unknown: UNKNOWN"
    )

    def _clean(raw: str) -> str:
        """Strip refusal prefixes and unhelpful boilerplate from Gemma's reply."""
        raw = raw.strip()
        if not raw or raw.upper().startswith("UNKNOWN"):
            return ""
        # Remove common Gemma preambles
        for prefix in (
            "i see ", "i can see ", "the image shows ", "this image shows ",
            "this appears to be ", "this is a ", "this is an ", "this is ",
            "the product is ", "it appears to be ", "based on the image, ",
            "looking at the image, ", "the image depicts ",
        ):
            if raw.lower().startswith(prefix):
                raw = raw[len(prefix):]
        # If Gemma returned a multi-sentence paragraph, take only the first sentence
        first_sentence = raw.split(".")[0].strip()
        return first_sentence if len(first_sentence) >= 3 else raw.strip()

    raw = ""

    # ── Attempt 1: /api/chat with full prompt ──────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(f"{OLLAMA_URL}/api/chat", json={
                "model": model,
                "messages": [{"role": "user", "content": FULL_PROMPT, "images": [b64]}],
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 60},
            })
            resp.raise_for_status()
            raw = resp.json().get("message", {}).get("content", "").strip()
    except Exception:
        pass

    result = _clean(raw)

    # ── Attempt 2: /api/generate (different code path in Ollama) ───────────
    if not result:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(f"{OLLAMA_URL}/api/generate", json={
                    "model": model,
                    "prompt": FULL_PROMPT,
                    "images": [b64],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 60},
                })
                resp.raise_for_status()
                raw = resp.json().get("response", "").strip()
            result = _clean(raw)
        except Exception:
            pass

    # ── Attempt 3: minimal prompt — last resort ────────────────────────────
    if not result:
        minimal = f"{hint_line}Name the home improvement product in this image. 3-5 words only."
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(f"{OLLAMA_URL}/api/chat", json={
                    "model": model,
                    "messages": [{"role": "user", "content": minimal, "images": [b64]}],
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 30},
                })
                resp.raise_for_status()
                raw = resp.json().get("message", {}).get("content", "").strip()
            result = _clean(raw)
        except Exception:
            pass

    # Cache result (including empty — avoids hammering Ollama for bad images)
    if len(_vision_cache) >= _VISION_CACHE_MAX:
        del _vision_cache[next(iter(_vision_cache))]
    _vision_cache[cache_key] = result
    return result


async def local_search(query: str) -> dict:
    """Fast fallback: offline keyword search from hd_store_data catalogue."""
    products = hd.search_fallback(query, max_results=6)
    for p in products:
        _session_products[p["id"]] = p

    if not products:
        return {
            "model": "local-keyword",
            "reply": f"No products matched '{query}'. Try a different keyword.",
            "products": [],
            "route": {},
            "source": "local_fallback",
        }

    route = hd.plan_route([p["id"] for p in products])
    lines = [f"Found {len(products)} product(s) for \"{query}\" (offline catalogue):"]
    for p in products[:4]:
        lines.append(f"  • {p['name']} ({p['brand']}) — {p['aisle']} — ${p['price']:.2f}")
    if len(products) > 4:
        lines.append(f"  … and {len(products)-4} more.")
    if route.get("estimated_minutes"):
        lines.append(f"\nRoute planned. Estimated walking time: ~{route['estimated_minutes']} min.")

    return {
        "model": "local-keyword",
        "reply": "\n".join(lines),
        "products": products,
        "route": route,
        "source": "local_fallback",
    }
