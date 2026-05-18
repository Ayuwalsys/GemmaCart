"""
Gemma 4 client via Ollama.

Capabilities used:
  • Function calling (tool use) — Gemma 4 natively supports native tool calls.
  • Multimodal vision — Gemma 4 27B is a vision-language model.
  • Streaming responses — for real-time UX.

Model priority (most capable first):
  1. gemma4:27b  — full-size, full vision
  2. gemma4:4b   — edge, fast, still multimodal
  3. gemma2:2b   — fallback if Gemma 4 not yet pulled
"""

from __future__ import annotations

import json
import base64
import httpx
import asyncio
from typing import Any

import store_data as db

# ── Ollama config ─────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434"
MODEL_PREFERENCE = ["gemma4:latest", "gemma4:31b", "gemma4:27b", "gemma4:4b", "gemma4:2b", "gemma2:2b", "gemma:7b"]

_resolved_model: str | None = None


async def resolve_model() -> str:
    """Return the best available Gemma model from Ollama."""
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
        # No preferred model found — use whatever is there
        _resolved_model = list(available)[0] if available else "gemma4:27b"
        return _resolved_model
    except Exception:
        _resolved_model = "gemma4:27b"
        return _resolved_model


# ── Tool definitions for Gemma 4 function calling ────────────────────────────

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Search the Costco Dedham store database for products matching a query. "
                "Use this whenever the user asks about finding a product, checking availability, "
                "or wants to know where something is located."
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
                        "description": "Maximum number of results (default 5)",
                        "default": 5,
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
                "Plan an optimized shopping route for multiple products. "
                "Returns the order to visit each product to minimise walking distance, "
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
            "description": "Get information about a specific store department or section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_name": {
                        "type": "string",
                        "description": "Department or section name (e.g. 'frozen', 'produce', 'electronics')",
                    },
                },
                "required": ["section_name"],
            },
        },
    },
]

# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> Any:
    if name == "search_products":
        return db.search_products(args.get("query", ""), args.get("max_results", 5))
    elif name == "plan_shopping_route":
        return db.plan_shopping_route(args.get("product_ids", []))
    elif name == "get_section_info":
        return db.get_section_info(args.get("section_name", ""))
    return {"error": f"Unknown tool: {name}"}


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are GemmaCart, an AI shopping assistant for Costco Wholesale in Dedham, MA.
Your job is to help shoppers find products quickly and navigate the store efficiently.

Guidelines:
- Always search for products using the search_products tool before answering location questions.
- For multiple items, call plan_shopping_route to give an optimised walking order.
- Give clear, concise directions (Section → Aisle → Side).
- Be friendly and conversational. Mention prices when helpful.
- If a product is not found, suggest the closest alternative.
- When a user uploads an image, identify what product(s) they are looking for and search accordingly.
- Keep responses brief — shoppers are on their feet.
"""

# ── Text query ────────────────────────────────────────────────────────────────

async def chat_with_tools(user_message: str) -> dict:
    """
    Send a text query to Gemma 4 with function-calling enabled.
    Returns { reply, products, route }
    """
    model = await resolve_model()
    messages = [{"role": "user", "content": user_message}]

    found_products: list[dict] = []
    route_data: dict = {}
    final_reply = ""

    async with httpx.AsyncClient(timeout=120) as client:
        # Agentic loop: keep calling until no more tool calls
        for _ in range(6):  # max 6 tool-use rounds
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
                # Final text response
                final_reply = msg.get("content", "")
                break

            # Execute each tool call
            messages.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args = tc["function"].get("arguments", {})
                if isinstance(fn_args, str):
                    try:
                        fn_args = json.loads(fn_args)
                    except json.JSONDecodeError:
                        fn_args = {}

                result = execute_tool(fn_name, fn_args)

                # Collect results for frontend
                if fn_name == "search_products" and isinstance(result, list):
                    for p in result:
                        if p not in found_products:
                            found_products.append(p)
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
    }


# ── Image query (multimodal) ──────────────────────────────────────────────────

async def chat_with_image(image_bytes: bytes, mime_type: str = "image/jpeg", hint: str = "") -> dict:
    """
    Send an image to Gemma 4's vision capability.
    Gemma first describes what product(s) it sees, then searches.
    """
    model = await resolve_model()
    b64 = base64.b64encode(image_bytes).decode()

    vision_prompt = (
        f"{hint}\n\n" if hint else ""
    ) + (
        "Look at this image carefully. Identify the grocery product(s), "
        "shopping list items, or product labels visible. "
        "List each item you see clearly, then search for them in the Costco store."
    )

    # Vision message with inline image
    vision_message = {
        "role": "user",
        "content": vision_prompt,
        "images": [b64],
    }

    messages = [vision_message]
    found_products: list[dict] = []
    route_data: dict = {}
    final_reply = ""

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

                result = execute_tool(fn_name, fn_args)

                if fn_name == "search_products" and isinstance(result, list):
                    for p in result:
                        if p not in found_products:
                            found_products.append(p)
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
    }


# ── Fallback: local keyword search (no Gemma) ─────────────────────────────────

async def local_search(query: str) -> dict:
    """Fast local keyword search — used when Ollama is unavailable or as pre-search."""
    products = db.search_products(query, max_results=6)
    if not products:
        return {
            "model": "local-keyword",
            "reply": f"No products matched '{query}'. Try a different keyword.",
            "products": [],
            "route": {},
        }

    names = ", ".join(p["name"] for p in products[:3])
    route = db.plan_shopping_route([p["id"] for p in products])

    lines = [f"Found {len(products)} product(s) for \"{query}\":"]
    for p in products[:3]:
        sec = db.SECTION_MAP.get(p["section"], {})
        lines.append(f"  • {p['name']} ({p['brand']}) — {p['aisle']} — ${p['price']}")
    if len(products) > 3:
        lines.append(f"  … and {len(products)-3} more.")
    if route["estimated_minutes"]:
        lines.append(f"\nOptimised route planned. Estimated walking time: ~{route['estimated_minutes']} min.")

    reply = "\n".join(lines)
    return {
        "model": "local-keyword",
        "reply": reply,
        "products": products,
        "route": route,
    }
