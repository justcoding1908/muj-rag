import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from rag_chain import build_chain, redis_client

# Groq's free tier shares one 200,000-token/day budget across every question asked —
# we hit this limit for real during testing. One client without a limit can burn through
# it for everyone else, so cap questions per IP per day. Backed by Redis (already running
# for the LLM cache) so the count survives a server restart, not an in-memory dict.
DAILY_LIMIT_PER_IP = int(os.getenv("DAILY_LIMIT_PER_IP", "30"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loading the embedding model and connecting to Chroma/Redis takes a few seconds —
    # do it once here at startup, not on every request.
    app.state.chain = build_chain(k=6)
    yield


app = FastAPI(title="MUJ Policy Assistant", lifespan=lifespan)

# Wide open for local development. Before this is used from a real frontend, restrict
# allow_origins to that frontend's actual domain instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class SourceOut(BaseModel):
    document: str
    page: int


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    found_in_document: bool


def client_ip(request: Request) -> str:
    # Deployed on Railway, every request arrives through their edge proxy, so
    # request.client.host would be the proxy's IP for every visitor — that turns the
    # per-IP limit into one shared global limit. Railway's proxy sets X-Forwarded-For to
    # the real visitor IP, so prefer that (its first entry) when present.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host


def check_rate_limit(client_ip: str):
    key = f"ratelimit:{client_ip}:{time.strftime('%Y-%m-%d')}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, 86400)
    if count > DAILY_LIMIT_PER_IP:
        raise HTTPException(status_code=429, detail=f"Daily question limit ({DAILY_LIMIT_PER_IP}) reached. Please try again tomorrow.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request):
    check_rate_limit(client_ip(request))

    try:
        result = request.app.state.chain.invoke(req.question)
    except Exception:
        # Don't leak internals (stack traces, API keys embedded in error messages) to the client.
        raise HTTPException(status_code=503, detail="The assistant is temporarily unavailable. Please try again shortly.")

    return AskResponse(
        answer=result.answer,
        sources=[SourceOut(document=s.document, page=s.page) for s in result.sources],
        found_in_document=result.found_in_document,
    )
