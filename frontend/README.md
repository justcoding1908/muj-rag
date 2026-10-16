# MUJ Policy Assistant — Frontend

A single-page chat UI for the [backend API](../README.md), built with Vite + React +
TypeScript. No routing, no state management library — just a chat box.

## Setup

```bash
npm install
npm run dev
```

By default it talks to the live production backend
(`https://muj-rag-production.up.railway.app`). To point it at a local backend instead,
create `.env.local`:

```
VITE_API_URL=http://localhost:8000
```

## How it talks to the backend

`src/api.ts` has the `fetch` call and the TypeScript types for the API's response shape
— kept in sync by hand with `api.py`'s `AskResponse`/`SourceOut` Pydantic models on the
backend. If those change, update both sides.

`VITE_API_URL` is read at **build time**, not runtime — Vite bakes it into the static JS
bundle when you run `npm run build`. There's no server-side config to change after
deploying; a different backend URL means a new build.

## Deploying (Vercel)

1. In Vercel, import the `justcoding1908/muj-rag` GitHub repo.
2. Set **Root Directory** to `frontend`. Vercel detects Vite and uses `npm run build` with
   the `dist` output folder.
3. Add the environment variable `VITE_API_URL` set to the backend's URL
   (`https://muj-rag-production.up.railway.app`). It is read at build time, so changing it
   means redeploying.
4. Every push to `main` redeploys automatically.

The backend allows any origin in CORS, so no backend change is needed for the Vercel domain.
