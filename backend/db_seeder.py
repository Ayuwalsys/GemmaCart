"""
GemmaCart – Product database seeder.

Seeds the local SQLite FTS5 database from three sources (in priority order):

  1. SerpAPI   – live Home Depot data (if SERPAPI_KEY is set)
  2. HD API    – Home Depot's own internal search endpoint (no key required)
  3. Fallback  – the curated static catalogue in hd_store_data.py

Run once to build the index, then re-run weekly to refresh prices/availability.

Usage
─────
  python db_seeder.py                    # seed default store (2665)
  python db_seeder.py --store 6902       # seed a different store
  python db_seeder.py --source hd        # force HD internal API only
  python db_seeder.py --source fallback  # force static catalogue only
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time

import httpx

# Resolve imports whether run as script or module
sys.path.insert(0, os.path.dirname(__file__))

import hd_store_data as hd
import product_db as db
from serpapi_client import SERPAPI_BASE, SERPAPI_KEY, _parse_serpapi_item

# ── Seed queries – one per major HD department ────────────────────────────────

SEED_QUERIES: list[str] = [
    # Power tools
    "cordless drill", "circular saw", "jigsaw", "angle grinder", "reciprocating saw",
    "impact driver", "random orbital sander", "rotary tool", "air compressor", "nail gun",
    # Hand tools
    "hammer", "wrench set", "screwdriver set", "pliers", "tape measure",
    "utility knife", "level", "chisel set", "hand saw",
    # Lumber & building materials
    "2x4 lumber", "plywood", "OSB board", "2x6 pressure treated", "furring strip",
    "drywall", "cement board", "concrete mix", "mortar mix",
    # Plumbing
    "PVC pipe", "copper pipe", "SharkBite fittings", "toilet", "bathroom faucet",
    "kitchen faucet", "showerhead", "wax ring", "pipe wrench", "plumber putty",
    # Electrical
    "12 gauge wire", "electrical outlet", "light switch", "circuit breaker",
    "LED bulb", "smart switch", "wire nuts", "conduit", "junction box",
    # Paint & finishing
    "interior paint", "exterior paint", "primer", "paint roller", "paint brush",
    "painter's tape", "paint tray", "wood stain", "polyurethane",
    # Hardware & fasteners
    "wood screws", "drywall screws", "lag bolts", "carriage bolts",
    "door hinges", "cabinet pulls", "drawer slides", "anchor bolts",
    # Flooring
    "ceramic tile", "vinyl plank flooring", "laminate flooring",
    "tile adhesive", "grout", "floor leveler", "subfloor underlayment",
    # Lighting
    "ceiling light fixture", "LED shop light", "outdoor flood light",
    "ceiling fan", "under cabinet light", "smart bulb",
    # Storage & organization
    "wire shelving", "storage bin", "garage cabinet", "pegboard",
    "tool chest", "wall shelf bracket",
    # Garden & outdoor
    "potting soil", "mulch", "garden hose", "soaker hose",
    "lawn fertilizer", "grass seed", "weed killer",
    # Appliances
    "refrigerator", "washing machine", "dishwasher", "water heater",
    # HVAC & comfort
    "HVAC filter", "programmable thermostat", "portable air conditioner",
    "window air conditioner", "dehumidifier",
    # Safety & security
    "smoke detector", "carbon monoxide detector", "fire extinguisher",
    "work gloves", "safety glasses",
    # Concrete & masonry
    "cinder block", "patio block", "retaining wall block", "brick",
    # Kitchen & bath
    "bathroom vanity", "toilet seat", "kitchen sink", "garbage disposal",
    "bathroom mirror", "towel bar",
    # Windows & doors
    "door lock", "door knob", "deadbolt", "door sweep", "weatherstrip",
    "window screen",
    # Décor & seasonal
    "ceiling tile", "crown molding", "baseboard trim", "holiday lights",
]


# ── HD internal API client ────────────────────────────────────────────────────

_HD_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.homedepot.com/",
}

_HD_SEARCH_URL = "https://www.homedepot.com/s/search/v1/products"


async def _fetch_hd_internal(
    client: httpx.AsyncClient,
    query: str,
    store_id: str,
    zip_code: str,
    page_size: int = 12,
) -> list[dict]:
    """
    Call Home Depot's internal search API.
    Returns parsed product dicts, or [] on any failure.
    """
    try:
        resp = await client.get(
            _HD_SEARCH_URL,
            params={
                "q": query,
                "storeId": store_id,
                "deliveryZip": zip_code,
                "pageSize": str(page_size),
                "startIndex": "0",
                "channel": "desktop",
                "ps": str(page_size),
            },
            headers=_HD_SEARCH_HEADERS,
            timeout=15,
        )
        if resp.status_code != 200:
            return []

        data = resp.json()

        # HD returns results under different keys depending on version
        raw = (
            data.get("products")
            or data.get("searchReport", {}).get("products", [])
            or data.get("data", {}).get("searchModel", {}).get("products", [])
            or []
        )

        products = []
        for item in raw[:page_size]:
            try:
                title = (
                    item.get("identifiers", {}).get("productLabel")
                    or item.get("title")
                    or item.get("name", "")
                )
                brand = (
                    item.get("identifiers", {}).get("brandName")
                    or item.get("brand", "")
                )
                price_info = item.get("pricing", {}) or {}
                price = (
                    price_info.get("value")
                    or price_info.get("specialPrice")
                    or price_info.get("originalPrice")
                    or 0.0
                )
                product_id = str(
                    item.get("identifiers", {}).get("storeSkuNumber")
                    or item.get("identifiers", {}).get("itemId")
                    or item.get("itemId")
                    or title[:20]
                )
                image = (
                    item.get("media", {}).get("images", [{}])[0].get("url", "")
                    if item.get("media", {}).get("images")
                    else ""
                )
                url = item.get("identifiers", {}).get("canonicalUrl", "")
                if url and not url.startswith("http"):
                    url = "https://www.homedepot.com" + url

                section = hd.infer_section(title, query)
                gx, gy = hd.product_grid_position(section, product_id)

                products.append({
                    "id":           product_id,
                    "name":         title,
                    "brand":        brand,
                    "category":     query.title(),
                    "section":      section,
                    "gx":           gx,
                    "gy":           gy,
                    "aisle":        hd.aisle_label(section, gx),
                    "price":        float(price) if price else 0.0,
                    "unit":         "each",
                    "rating":       None,
                    "num_reviews":  None,
                    "image":        image,
                    "url":          url,
                    "tags":         [w.lower() for w in title.split()[:6]],
                    "source":       "hd_internal",
                })
            except Exception:
                continue

        return products

    except Exception:
        return []


# ── SerpAPI fetcher ───────────────────────────────────────────────────────────

async def _fetch_serpapi(
    client: httpx.AsyncClient,
    query: str,
    store_id: str,
    zip_code: str,
    page_size: int = 12,
) -> list[dict]:
    """Call SerpAPI and return parsed products."""
    if not SERPAPI_KEY:
        return []
    try:
        resp = await client.get(
            SERPAPI_BASE,
            params={
                "engine":       "home_depot",
                "q":            query,
                "store_id":     store_id,
                "delivery_zip": zip_code,
                "api_key":      SERPAPI_KEY,
                "ps":           str(page_size),
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        raw = (
            data.get("products_results")
            or data.get("organic_results")
            or data.get("products", [])
        )
        return [_parse_serpapi_item(item, query) for item in raw[:page_size]]
    except Exception:
        return []


# ── Main seeder ───────────────────────────────────────────────────────────────

async def seed(
    store_id: str = "2665",
    zip_code: str = "02132",
    source: str = "auto",          # "auto" | "serpapi" | "hd" | "fallback"
    page_size: int = 12,
    delay: float = 1.0,            # seconds between requests (rate limit)
    quiet: bool = False,
) -> dict:
    """
    Seed the product database.

    source="auto"  tries: serpapi → hd → fallback (per query)
    Returns a summary dict: {total, serpapi, hd_internal, fallback, skipped}
    """
    db.init_db()

    counts = {"total": 0, "serpapi": 0, "hd_internal": 0, "fallback": 0, "skipped": 0}
    start = time.time()

    # Always seed the static fallback catalogue first (instant, zero cost)
    if source in ("auto", "fallback"):
        n = db.upsert_products(hd.FALLBACK_PRODUCTS, store_id)
        counts["fallback"] += n
        counts["total"] += n
        if not quiet:
            print(f"  [fallback] {n} static products indexed")

    if source == "fallback":
        return counts

    queries = SEED_QUERIES
    total_q = len(queries)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for i, query in enumerate(queries, 1):
            if not quiet:
                print(f"  [{i}/{total_q}] '{query}'", end="  ", flush=True)

            products: list[dict] = []
            src_used = ""

            if source in ("auto", "serpapi") and SERPAPI_KEY:
                products = await _fetch_serpapi(client, query, store_id, zip_code, page_size)
                src_used = "serpapi"

            if not products and source in ("auto", "hd"):
                products = await _fetch_hd_internal(client, query, store_id, zip_code, page_size)
                src_used = "hd_internal"

            if products:
                n = db.upsert_products(products, store_id)
                counts[src_used] += n
                counts["total"] += n
                if not quiet:
                    print(f"→ {n} products ({src_used})")
            else:
                counts["skipped"] += 1
                if not quiet:
                    print("→ no results (skipped)")

            # Polite rate limit
            await asyncio.sleep(delay)

    elapsed = time.time() - start
    if not quiet:
        print(f"\n✓ Seeding complete in {elapsed:.1f}s")
        print(f"  Total indexed : {counts['total']}")
        print(f"  From SerpAPI  : {counts['serpapi']}")
        print(f"  From HD API   : {counts['hd_internal']}")
        print(f"  From fallback : {counts['fallback']}")
        print(f"  Skipped       : {counts['skipped']}")
        print(f"  DB total      : {db.product_count(store_id)} products")

    return counts


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed GemmaCart product database")
    parser.add_argument("--store",  default="2665",  help="HD store ID (default: 2665)")
    parser.add_argument("--zip",    default="02132", help="Delivery ZIP code (default: 02132)")
    parser.add_argument(
        "--source",
        choices=["auto", "serpapi", "hd", "fallback"],
        default="auto",
        help="Data source: auto (default) | serpapi | hd | fallback",
    )
    parser.add_argument("--page-size", type=int, default=12, help="Results per query (default: 12)")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests (default: 1.0)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-query output")
    args = parser.parse_args()

    print(f"GemmaCart DB Seeder")
    print(f"  Store ID : {args.store}")
    print(f"  ZIP      : {args.zip}")
    print(f"  Source   : {args.source}")
    print(f"  Queries  : {len(SEED_QUERIES)}")
    print(f"  Page size: {args.page_size}")
    print()

    asyncio.run(
        seed(
            store_id=args.store,
            zip_code=args.zip,
            source=args.source,
            page_size=args.page_size,
            delay=args.delay,
            quiet=args.quiet,
        )
    )
