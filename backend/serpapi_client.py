"""
SerpAPI – Home Depot product search integration.

SerpAPI wraps Home Depot's live website (real prices, real inventory,
real product images) and returns structured JSON.

Docs: https://serpapi.com/home-depot-search-api
Endpoint: GET https://serpapi.com/search?engine=home_depot&...
"""

from __future__ import annotations
import os
import httpx

# Load .env file if present (no extra dependencies needed)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from hd_store_data import (
    infer_section, product_grid_position, aisle_label,
    search_fallback, STORE_META,
)
import product_db as _pdb

# Ensure the DB schema exists on first import (idempotent)
_pdb.init_db()

# ── Config ────────────────────────────────────────────────────────────────────
SERPAPI_KEY  = os.getenv("SERPAPI_KEY", "")
SERPAPI_BASE = "https://serpapi.com/search"

# ── Mutable store context (updated dynamically when user changes ZIP) ─────────
_current_store: dict = {
    "store_id":   os.getenv("HD_STORE_ID", STORE_META["store_id"]),
    "zip":        os.getenv("HD_ZIP", "02132"),
    "name":       STORE_META["name"],
    "address":    STORE_META["address"],
    "phone":      STORE_META["phone"],
    "google_maps_url": STORE_META["google_maps_url"],
}


def get_current_store() -> dict:
    return dict(_current_store)


def set_current_store(store: dict) -> None:
    _current_store.update(store)


# ── Home Depot store locator (no extra API key needed) ────────────────────────

async def locate_store_by_zip(zip_code: str) -> dict:
    """
    Find the nearest Home Depot store for a given ZIP code.
    Uses Home Depot's public store-locator endpoint.
    Falls back to a SerpAPI-based approach if HD's endpoint is unavailable.
    """
    zip_code = zip_code.strip().replace(" ", "")

    # Try HD's own store-locator JSON API (used by their website)
    try:
        async with httpx.AsyncClient(
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GemmaCart/1.0)"},
            follow_redirects=True,
        ) as client:
            resp = await client.get(
                "https://www.homedepot.com/l/API/store/search",
                params={"storeSearch": zip_code, "radius": "25", "resultsCount": "1"},
            )
            data = resp.json()

        stores = (
            data.get("stores")
            or data.get("storeSearchResults")
            or data.get("results")
            or []
        )
        if stores:
            s = stores[0]
            store_id = str(
                s.get("storeId") or s.get("storeNumber") or s.get("store_id") or ""
            )
            address_obj = s.get("address") or s.get("storeAddress") or {}
            street = address_obj.get("street") or address_obj.get("address1") or ""
            city   = address_obj.get("city", "")
            state  = address_obj.get("state", "")
            postal = address_obj.get("postalCode") or address_obj.get("zip") or zip_code
            phone  = s.get("phone") or s.get("storePhone") or ""
            name   = s.get("storeName") or f"The Home Depot – {city}, {state}"

            # Extract lat/lng — HD locator returns them at top-level or inside coordinates{}
            coords = s.get("coordinates") or s.get("geoPoint") or {}
            lat = s.get("latitude") or s.get("lat") or coords.get("latitude") or coords.get("lat")
            lng = s.get("longitude") or s.get("lng") or coords.get("longitude") or coords.get("lng")

            address = f"{street}, {city}, {state} {postal}".strip(", ")
            maps_url = (
                f"https://www.google.com/maps/search/?api=1"
                f"&query={name.replace(' ', '+')}+{city}+{state}"
            )

            result = {
                "store_id": store_id,
                "zip": postal,
                "name": name,
                "address": address,
                "phone": phone,
                "google_maps_url": maps_url,
                "source": "hd_locator",
            }
            if lat is not None:
                result["lat"] = float(lat)
            if lng is not None:
                result["lng"] = float(lng)
            return result
    except Exception:
        pass  # Fall through to SerpAPI fallback

    # Fallback: use SerpAPI to do a generic search and infer store from results
    if SERPAPI_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    SERPAPI_BASE,
                    params={
                        "engine": "home_depot",
                        "q": "hammer",
                        "delivery_zip": zip_code,
                        "api_key": SERPAPI_KEY,
                        "ps": "1",
                    },
                )
                data = resp.json()
            # SerpAPI doesn't return store meta directly, but we can confirm
            # the ZIP is valid if we get results
            raw = (
                data.get("products_results")
                or data.get("organic_results")
                or data.get("products", [])
            )
            if raw:
                name = f"The Home Depot – near {zip_code}"
                maps_url = (
                    f"https://www.google.com/maps/search/?api=1"
                    f"&query=Home+Depot+near+{zip_code}"
                )
                return {
                    "store_id": zip_code,   # use ZIP as proxy store_id
                    "zip": zip_code,
                    "name": name,
                    "address": f"Near {zip_code}",
                    "phone": "",
                    "google_maps_url": maps_url,
                    "source": "zip_only",
                }
        except Exception:
            pass

    return {"error": f"No Home Depot store found near ZIP {zip_code}"}


# ── SerpAPI response → our product schema ────────────────────────────────────

def _parse_price(raw) -> float:
    """Parse SerpAPI price which may be '$12.98', 12.98, or None."""
    if raw is None:
        return 0.0
    if isinstance(raw, (int, float)):
        return float(raw)
    # Strip currency symbols, commas, whitespace  e.g. "$1,298.00"
    cleaned = str(raw).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _clean_hd_url(raw: str, name: str = "", product_id: str = "") -> str:
    """Return a publicly-accessible Home Depot product page URL.

    SerpAPI sometimes returns internal apionline.homedepot.com URLs that
    return Access Denied. We convert them to the public www.homedepot.com
    equivalents and fall back to a search URL when nothing else is available.
    """
    import re as _re
    if not raw:
        slug = _re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-")
        if slug and product_id:
            return f"https://www.homedepot.com/p/{slug}/{product_id}"
        if slug:
            return f"https://www.homedepot.com/s/{slug}"
        return ""
    # Fix internal API host → public host
    url = _re.sub(r"https?://apionline\.homedepot\.com/p/sets/", "https://www.homedepot.com/p/", raw)
    url = _re.sub(r"https?://apionline\.homedepot\.com", "https://www.homedepot.com", url)
    # Ensure HTTPS
    url = _re.sub(r"^http://", "https://", url)
    return url


def _parse_serpapi_item(item: dict, query: str = "") -> dict:
    """
    Convert a SerpAPI Home Depot product dict to our internal schema.

    Real SerpAPI HD response shape (verified 2026-04):
      product_id, title, brand, price (string "$x.xx"),
      rating (float, top-level), reviews (int count, top-level),
      thumbnails (list of lists), link
    """
    title = item.get("title", "Unknown Product")
    brand = item.get("brand") or item.get("source") or ""

    price = _parse_price(item.get("price"))

    # rating/reviews: can be top-level scalars OR nested dicts
    reviews_raw = item.get("reviews")
    if isinstance(reviews_raw, dict):
        rating      = reviews_raw.get("rating")
        num_reviews = reviews_raw.get("count")
    else:
        rating      = item.get("rating")
        num_reviews = reviews_raw if isinstance(reviews_raw, int) else None

    # thumbnails: list of lists  e.g. [["url_65px", "url_100px", ...], ...]
    thumbnails = item.get("thumbnails") or []
    image = ""
    if thumbnails and isinstance(thumbnails[0], list) and thumbnails[0]:
        image = thumbnails[0][-1]   # largest variant
    elif thumbnails and isinstance(thumbnails[0], str):
        image = thumbnails[0]
    image = image or item.get("thumbnail", "")

    breadcrumb = " ".join(item.get("breadcrumbs", []))
    section    = infer_section(title, breadcrumb + " " + query)
    product_id = str(item.get("product_id") or item.get("item_id") or title[:20])
    gx, gy     = product_grid_position(section, product_id)

    return {
        "id":          product_id,
        "name":        title,
        "brand":       brand,
        "category":    breadcrumb.split(" > ")[-1] if breadcrumb else section.replace("_", " ").title(),
        "section":     section,
        "gx":          gx,
        "gy":          gy,
        "aisle":       aisle_label(section, gx, gy),
        "price":       price,
        "unit":        item.get("unit") or "each",
        "rating":      rating,
        "num_reviews": num_reviews,
        "image":       image,
        "url":         _clean_hd_url(item.get("link") or item.get("product_url") or "", title, product_id),
        "tags":        [w.lower() for w in title.split()[:6]],
        "source":      "serpapi_live",
    }


# ── Main search function ──────────────────────────────────────────────────────

async def search_home_depot(
    query: str,
    max_results: int = 8,
    store_id: str | None = None,
    zip_code: str | None = None,
) -> tuple[list[dict], str]:
    """
    Search Home Depot products.

    Priority order (DB-first architecture):
      1. Local SQLite FTS5 DB  – instant, zero cost, seeded by db_seeder.py
      2. SerpAPI               – live data on cache miss (if key configured)
      3. Static fallback       – offline catalogue in hd_store_data.py

    Returns (products, source) where source is one of:
      'local_db'       – SQLite FTS5 hit (primary path after seeding)
      'serpapi_live'   – real-time SerpAPI result (cache miss, then stored in DB)
      'local_fallback' – static catalogue (no key / quota exceeded / offline)
    """
    store = get_current_store()
    sid   = store_id or store["store_id"]
    zip_  = zip_code or store["zip"]

    # Normalise store_id: ZIP codes used as fallback IDs ("02126", "02132", …)
    # are 5-digit strings, not real 4-digit HD store IDs — fall back to default DB store.
    DEFAULT_STORE_ID = "2665"
    db_sid = sid if (sid and len(sid) == 4 and sid.isdigit()) else DEFAULT_STORE_ID

    # ── 1. Local DB (primary) ──────────────────────────────────────────────
    db_results = _pdb.search_products(query, max_results, store_id=db_sid)
    if db_results:
        return db_results, "local_db"

    # ── 2. SerpAPI (cache miss) ────────────────────────────────────────────
    if SERPAPI_KEY:
        params = {
            "engine":       "home_depot",
            "q":            query,
            "store_id":     sid,
            "delivery_zip": zip_,
            "api_key":      SERPAPI_KEY,
            "ps":           str(max_results),
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(SERPAPI_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()

            raw = (
                data.get("products_results")
                or data.get("organic_results")
                or data.get("products", [])
            )
            if raw:
                products = [_parse_serpapi_item(item, query) for item in raw[:max_results]]
                # Persist to DB so next identical/similar query hits the cache
                _pdb.upsert_products(products, store_id=sid)
                return products, "serpapi_live"

        except httpx.HTTPStatusError as e:
            if e.response.status_code != 429:
                raise
            # quota exceeded – fall through to static fallback
        except Exception:
            pass  # network error – fall through

    # ── 3. Static fallback ─────────────────────────────────────────────────
    return search_fallback(query, max_results), "local_fallback"


async def get_serpapi_status() -> dict:
    """Check remaining SerpAPI quota."""
    if not SERPAPI_KEY:
        return {"configured": False, "message": "SERPAPI_KEY not set"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://serpapi.com/account",
                params={"api_key": SERPAPI_KEY},
            )
            d = resp.json()
            return {
                "configured": True,
                "plan": d.get("plan_name"),
                "searches_used": d.get("this_month_usage"),
                "searches_left": d.get("plan_searches_left"),
            }
    except Exception as e:
        return {"configured": True, "error": str(e)}
