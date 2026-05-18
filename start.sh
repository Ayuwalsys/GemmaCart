#!/usr/bin/env bash
# GemmaCart – Quick start script
# Usage: ./start.sh [model]
# Example: ./start.sh gemma4:27b

set -e

MODEL=${1:-gemma4:31b}
PORT=${PORT:-8000}

echo "╔══════════════════════════════════════════════╗"
echo "║     GemmaCart – Costco Product Navigator     ║"
echo "║     Powered by Gemma 4 · Ollama · FastAPI    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Check Ollama
if ! command -v ollama &>/dev/null; then
  echo "⚠  Ollama not found. Install from https://ollama.com"
  exit 1
fi

# Check if Ollama is running
if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
  echo "▶  Starting Ollama service…"
  ollama serve &
  sleep 3
fi

# Pull model if needed
INSTALLED=$(ollama list 2>/dev/null | awk '{print $1}' | grep -F "$MODEL" || true)
if [ -z "$INSTALLED" ]; then
  echo "📥  Pulling $MODEL (this may take a few minutes)…"
  ollama pull "$MODEL"
fi

echo "✅  Ollama running · Model: $MODEL"
echo ""

# Install Python deps
echo "📦  Installing Python dependencies…"
pip install -q -r requirements.txt

echo ""
echo "🚀  Starting GemmaCart API on http://localhost:$PORT"
echo "🌐  Open your browser at: http://localhost:$PORT"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

cd backend
uvicorn app:app --host 0.0.0.0 --port "$PORT" --reload
