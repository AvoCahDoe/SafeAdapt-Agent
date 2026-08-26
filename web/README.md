# SafeAdapt Web

Next.js showcase for SafeAdapt (landing, results gallery, interactive try page).

## Local

```bash
cd web
cp .env.example .env.local
# set NEXT_PUBLIC_API_URL to local uvicorn or Render URL
npm install
npm run dev
```

## Deploy

Vercel project with root directory `web/`. Set `NEXT_PUBLIC_API_URL` to the Render FastAPI service URL.
