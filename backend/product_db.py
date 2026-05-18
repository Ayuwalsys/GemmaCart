"""
GemmaCart – SQLite + FTS5 product database.

Schema
──────
products        – canonical product rows (id, name, brand, price, aisle, …)
products_fts    – FTS5 virtual table kept in sync manually

Why FTS5?
  • BM25-ranked full-text search with zero extra dependencies
  • WAL mode → concurrent reads + writes without blocking
  • Seed once (db_seeder.py), serve forever – no per-query API cost
"""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "products.db")


# ── Connection ────────────────────────────────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS products (
    id           TEXT NOT NULL,
    store_id     TEXT NOT NULL DEFAULT '2665',
    name         TEXT NOT NULL,
    brand        TEXT,
    category     TEXT,
    section      TEXT,
    gx           INTEGER,
    gy           INTEGER,
    aisle        TEXT,
    price        REAL,
    unit         TEXT,
    rating       REAL,
    num_reviews  INTEGER,
    image        TEXT,
    url          TEXT,
    tags         TEXT,          -- JSON array stored as text
    source       TEXT,
    last_updated TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (id, store_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
    id        UNINDEXED,
    store_id  UNINDEXED,
    name,
    brand,
    category,
    section,
    aisle,
    tags,
    tokenize = "porter ascii"
);
"""


def init_db() -> None:
    """Create tables if they don't exist. Safe to call multiple times."""
    with _get_conn() as conn:
        conn.executescript(_DDL)


# ── Write ─────────────────────────────────────────────────────────────────────

def upsert_products(products: list[dict], store_id: str = "2665") -> int:
    """
    Insert or replace products in bulk.
    Keeps FTS index in sync manually (avoids trigger complexity with OR REPLACE).
    Returns count of rows written.
    """
    if not products:
        return 0

    written = 0
    with _get_conn() as conn:
        for p in products:
            pid = str(p.get("id", ""))
            if not pid:
                continue

            tags_json = json.dumps(p.get("tags") or [], ensure_ascii=False)

            # Remove stale FTS entry before replacing the product row
            conn.execute(
                "DELETE FROM products_fts WHERE id=? AND store_id=?",
                (pid, store_id),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO products
                  (id, store_id, name, brand, category, section, gx, gy,
                   aisle, price, unit, rating, num_reviews, image, url,
                   tags, source, last_updated)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                """,
                (
                    pid, store_id,
                    p.get("name", ""), p.get("brand", ""),
                    p.get("category", ""), p.get("section", ""),
                    p.get("gx"), p.get("gy"),
                    p.get("aisle", ""), p.get("price"),
                    p.get("unit", "each"), p.get("rating"),
                    p.get("num_reviews"), p.get("image", ""),
                    p.get("url", ""), tags_json,
                    p.get("source", "seeded"),
                ),
            )

            # Re-insert into FTS with fresh content
            conn.execute(
                """
                INSERT INTO products_fts
                  (id, store_id, name, brand, category, section, aisle, tags)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    pid, store_id,
                    p.get("name", ""), p.get("brand", ""),
                    p.get("category", ""), p.get("section", ""),
                    p.get("aisle", ""), tags_json,
                ),
            )
            written += 1

    return written


# ── Read ──────────────────────────────────────────────────────────────────────

_FTS_STOP = frozenset({
    "a","an","the","and","or","in","of","to","for","with","by","at","on",
    "is","are","was","were","it","its","this","that","be","as","from",
})

def search_products(
    query: str,
    max_results: int = 8,
    store_id: str = "2665",
) -> list[dict]:
    """
    BM25-ranked FTS5 search. Falls back to LIKE on FTS parse errors.
    Returns a list of product dicts (same schema as SerpAPI results).
    Multi-word queries use AND (implicit FTS5 AND) to avoid cross-category matches.
    """
    with _get_conn() as conn:
        # Filter stop words then use implicit AND (space-separated = AND in FTS5)
        all_tokens = [w.strip() for w in query.split() if w.strip()]
        tokens = [t for t in all_tokens if t.lower() not in _FTS_STOP]
        if not tokens:
            tokens = all_tokens  # fallback: no stop words filtered
        # Implicit AND: space-separated quoted terms in FTS5 require all terms
        fts_query = " ".join(f'"{t}"' for t in tokens) if tokens else query

        try:
            rows = conn.execute(
                """
                SELECT p.*
                FROM products p
                JOIN products_fts f ON f.id = p.id AND f.store_id = p.store_id
                WHERE products_fts MATCH ? AND p.store_id = ?
                ORDER BY rank
                LIMIT ?
                """,
                (fts_query, store_id, max_results),
            ).fetchall()
        except sqlite3.OperationalError:
            # FTS parse failure (e.g. special chars) – fall back to LIKE
            like = f"%{query}%"
            rows = conn.execute(
                """
                SELECT * FROM products
                WHERE (name LIKE ? OR brand LIKE ? OR category LIKE ?)
                  AND store_id = ?
                ORDER BY rating DESC
                LIMIT ?
                """,
                (like, like, like, store_id, max_results),
            ).fetchall()

    return [_row_to_dict(r) for r in rows]


def get_product(pid: str, store_id: str = "2665") -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM products WHERE id=? AND store_id=?",
            (pid, store_id),
        ).fetchone()
    return _row_to_dict(row) if row else None


def product_count(store_id: str = "2665") -> int:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM products WHERE store_id=?", (store_id,)
        ).fetchone()[0]


def all_products(store_id: str = "2665") -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE store_id=? ORDER BY section, name",
            (store_id,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    # Deserialise tags back to list
    raw_tags = d.get("tags")
    try:
        d["tags"] = json.loads(raw_tags) if raw_tags else []
    except (json.JSONDecodeError, TypeError):
        d["tags"] = []
    return d


# ── CLI self-test ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    n = product_count()
    print(f"DB at {DB_PATH} — {n} products indexed")
    if n:
        hits = search_products("drill", max_results=3)
        print("Sample search 'drill':")
        for h in hits:
            print(f"  {h['name']} | {h['aisle']} | ${h['price']}")
