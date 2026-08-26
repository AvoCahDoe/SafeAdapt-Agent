# SafeAdapt Web

Portfolio demo for SafeAdapt — Next.js on Vercel, FastAPI on Render.

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Simple landing |
| `/results` | Charts + interpretations |
| `/try` | Guided interactive runs |
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

## Deploy checklist

1. **Render** — `safeadapt-api` from repo root (`render.yaml`); set `DEEPSEEK_API_KEY`, `CORS_ORIGINS` to your Vercel domain(s).
2. **Vercel** — project root directory `web/`; set `NEXT_PUBLIC_API_URL=https://safeadapt-api.onrender.com`.
3. Smoke: `/`, `/results`, `/docs`, mock run on `/try`.

Regenerate showcase: `PYTHONPATH=src python scripts/export_showcase.py`
