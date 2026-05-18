# GemmaCart — AI In-Store Shopping Assistant

> Kaggle Gemma 4 Competition Submission  
> Gemma 4 × Ollama × FastAPI × SerpAPI

GemmaCart is a mobile-first AI shopping assistant that helps Home Depot customers find products and navigate to their exact physical location inside the store — no GPS or printed map required.

---

## How It Works

```
Mobile Browser  →  FastAPI Backend  →  Gemma 4 (Ollama)
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                      search_products  get_navigation  plan_route
                              │               │               │
                        SQLite FTS5    Aisle-coordinate   Nearest-
                        (< 5 ms) or    turn-by-turn nav  neighbour TSP
                        SerpAPI live
```

1. **Auto check-in** — browser geofence detects when you're inside the store
2. **Chat naturally** — *"Where can I find a cordless drill under $100?"*
3. **Gemma 4 reasons** — calls `search_products` → gets real HD inventory + prices
4. **Exact location** — *"Tools · Aisle 07, Bay 3 — walk right 2 aisles, halfway to the back"*
5. **Turn-by-turn** — step-by-step walking directions using the orange overhead aisle signs
6. **Multi-stop route** — `plan_shopping_route` sorts your list by aisle order, minimising backtracking
7. **Photo search** — point your camera at any product → Gemma vision identifies it and finds it in-store
8. **My Aisle** — tap 📍, read the sign above you, enter the number → directions recalculate instantly

---

## Navigation Without GPS

Home Depot aisles are numbered 1–35 on orange overhead signs — a physical coordinate system built into every store. GemmaCart uses two numbers to pinpoint any product:

| Coordinate | What it means | Range |
|---|---|---|
| **Aisle** | Left-right position across the store | 1–35 (or G1–G4 for garden) |
| **Bay** | Front-to-back depth within the aisle | 1 = near registers · 6 = back wall |

The `get_navigation_directions` Gemma tool converts aisle/bay deltas into plain-English walking steps. When a customer taps **📍 My Aisle** and enters the number on the sign above them, all directions recalculate from their current position.

---

## Project Structure

```
GemmaCart/
├── backend/
│   ├── app.py              # FastAPI — all REST endpoints
│   ├── hd_gemma_client.py  # Gemma 4 tool-calling + vision pipeline
│   ├── hd_store_data.py    # Store layout, aisle-coordinate engine, route planner
│   ├── serpapi_client.py   # SerpAPI integration + DB-first search
│   ├── product_db.py       # SQLite FTS5 product database
│   └── db_seeder.py        # Seeds ~1,378 products from SerpAPI
├── frontend/
│   └── index.html          # Mobile chat UI — geofence, voice, camera, nav
├── gemmacart_notebook.ipynb # Kaggle competition notebook
├── Dockerfile
├── docker-compose.yml
├── start.sh                # One-command local launcher
└── requirements.txt
```

---

## Quickstart

### Option 1 — Shell script (recommended for local dev)

```bash
# 1. Clone
git clone https://github.com/Ayuwalsys/GemmaCart.git
cd GemmaCart

# 2. Add your API key (SerpAPI is optional — falls back to offline catalogue)
cp backend/.env.example backend/.env
# edit backend/.env and set SERPAPI_KEY

# 3. Start (installs deps, pulls Gemma 4, launches API)
./start.sh

# Open http://localhost:8000
```

### Option 2 — Docker Compose

```bash
docker compose up --build
# Open http://localhost:8000
```

### Option 3 — Manual

```bash
# Terminal 1 — Ollama
ollama serve
ollama pull gemma4:4b      # or gemma4:12b / gemma4:27b

# Terminal 2 — API
pip install -r requirements.txt
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

---

## Environment Variables

Create `backend/.env`:

```env
# Required for live Home Depot product data (free tier: 100 searches/month)
SERPAPI_KEY=your_serpapi_key_here

# Optional — defaults to the Dedham, MA store
HD_STORE_ID=2665
HD_ZIP=02026
```

Get a free SerpAPI key at [serpapi.com](https://serpapi.com). Without it, GemmaCart uses the built-in offline product catalogue.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Mobile web UI |
| `POST` | `/api/search/text` | Natural-language product search (Gemma 4 + SerpAPI) |
| `POST` | `/api/search/image` | Upload photo → identify + locate product |
| `POST` | `/api/route/plan` | Optimise multi-stop shopping route |
| `GET` | `/api/store/meta` | Active store info + Google Maps link |
| `GET` | `/api/store/locate?zip=02026` | Find nearest HD by ZIP + update active store |
| `GET` | `/api/store/layout` | Grid sections for map render |
| `GET` | `/api/model/status` | Gemma model status |
| `GET` | `/api/serpapi/status` | SerpAPI quota |

Interactive docs: `http://localhost:8000/docs`

---

## Seed the Product Database

```bash
cd backend
python db_seeder.py
# Indexes ~1,378 products across 18 departments in ~5 minutes
# After seeding, all searches hit SQLite first (< 5 ms, zero API cost)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| AI model | Gemma 4 via Ollama (function calling + vision) |
| Backend | Python 3.11 · FastAPI · uvicorn |
| Database | SQLite FTS5 (BM25 full-text search) |
| Live data | SerpAPI — Home Depot product API |
| Frontend | Vanilla JS · mobile-first · PWA-ready |
| Navigation | Custom aisle-coordinate engine (no GPS) |
| Voice | Web Speech API (text-to-speech directions) |
| Containerisation | Docker · Docker Compose |

---

## Why Gemma 4?

- **Function calling** — autonomously chains `search_products` → `get_navigation_directions` → `plan_shopping_route` without prompting
- **Vision** — identifies products from photos, handwritten lists, and shelf labels
- **Runs locally** — zero per-query cost, fully private, works offline after DB seeding
- **Conversational** — handles follow-ups, budget constraints, and multi-item planning naturally

---

## License

MIT
