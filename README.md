# SafeAdapt

Research prototype for studying **alignment drift in continually interacting LLM agents**.

## Status

**Phase 10 (LLM)** — OpenAI-compatible (DeepSeek), Ollama, and independent LLM judge.

Phases 1–10 complete for the research prototype pipeline (mock + real LLM).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env       # set DEEPSEEK_API_KEY / OPENAI_API_KEY
```

## Usage

```bash
# Mock (no API)
safeadapt run configs/experiments/filesystem_drift.yaml
safeadapt matrix configs/experiments/matrix_dev.yaml

# DeepSeek (OpenAI-compatible)
safeadapt run configs/experiments/filesystem_deepseek.yaml

# Ollama (local)
safeadapt run configs/experiments/filesystem_ollama.yaml
```

## Web showcase

Public UI (Next.js on Vercel) + API (FastAPI on Render):

```bash
# API
pip install -e ".[dev]" && pip install -r api/requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd web && cp .env.example .env.local
# set NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm install && npm run dev
```

Regenerate committed showcase plots: `PYTHONPATH=src python scripts/export_showcase.py`

## Tests

```bash
pytest -v
```

See `plan.md` for the full specification.
