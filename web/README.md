# SafeAdapt Web

Next.js frontend (Vercel) + FastAPI backend (Render) for SafeAdapt.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing |
| `/results` | Charts + interpretations |
| `/try` | Interactive experiment runner |
| `/docs` | Motivation, formulas, setup, figures |

## Local

```bash
# API (repo root)
pip install -e ".[dev]" && pip install -r api/requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend
cd web
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
npm install && npm run dev
```

## Deploy

1. **Render** — web service from repo root (`render.yaml`); set `DEEPSEEK_API_KEY`, `CORS_ORIGINS`.
2. **Vercel** — root directory `web/`; set `NEXT_PUBLIC_API_URL` to the Render URL.

Regenerate showcase: `PYTHONPATH=src python scripts/export_showcase.py`
