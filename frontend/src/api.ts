// Mirrors api.py's AskResponse/SourceOut Pydantic models exactly.
export interface Source {
  document: string;
  page: number;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
  found_in_document: boolean;
}

// Set via frontend/.env (local dev) or the VITE_API_URL env var at build time
// (Railway). Falls back to the live backend so `npm run dev` works with no setup.
const API_URL = import.meta.env.VITE_API_URL ?? "https://muj-rag-production.up.railway.app";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const res = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    // api.py returns {"detail": "..."} for every error case (422 validation,
    // 429 rate limit, 503 upstream failure) — surface that message directly.
    const body = await res.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`;
    throw new ApiError(res.status, detail);
  }

  return res.json();
}
