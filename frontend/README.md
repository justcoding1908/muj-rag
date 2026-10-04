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

## Deploying (Railway)

This runs as a second Railway service in the same project as the backend:

1. In Railway, add a new service from the same `justcoding1908/muj-rag` GitHub repo.
2. Set its **Root Directory** to `frontend` (Settings → Source) — this is what tells
   Railway to use `frontend/Dockerfile` instead of the backend's root-level one.
3. Set `VITE_API_URL` to the backend's real Railway URL in this service's **Variables**
   tab. Railway passes service variables through as Docker build args automatically
   when the Dockerfile declares a matching `ARG` (it does here) — if the build
   somehow doesn't pick it up, look for a separate build-args section in Railway's
   current UI; this has moved around between versions.
4. Generate a public domain for this service once it deploys.

The Dockerfile is a two-stage build: compiles the Vite app in a `node:22-slim` build
stage, then serves the static output with [`serve`](https://www.npmjs.com/package/serve)
in a second, smaller stage.
