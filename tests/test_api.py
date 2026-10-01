"""API-level tests via FastAPI's TestClient. The real LLM chain is replaced with a stub,
so these run free and fast — no Groq calls. They check request validation and the
rate limiter, neither of which depends on what the LLM actually says.

These do need a reachable Redis (the same one api.py uses for its rate-limit counter) —
not "zero dependency," but still free; no LLM tokens are spent.
"""
import pytest
from fastapi.testclient import TestClient
from rag_chain import RAGAnswer, Source, redis_client

FAKE_ANSWER = RAGAnswer(
    answer="75%",
    sources=[Source(document="Academic Rules and Regulations 2024", page=5)],
    found_in_document=True,
)


class FakeChain:
    def invoke(self, question):
        return FAKE_ANSWER


@pytest.fixture(autouse=True)
def clean_rate_limit_keys():
    """Isolate each test's rate-limit counters from real usage and from each other."""
    before = set(redis_client.keys("ratelimit:*"))
    yield
    new_keys = set(redis_client.keys("ratelimit:*")) - before
    if new_keys:
        redis_client.delete(*new_keys)


@pytest.fixture
def client(monkeypatch):
    # Patch build_chain before the app starts, so lifespan() picks up the stub instead
    # of loading the real embedding model and calling Groq.
    monkeypatch.setattr("api.build_chain", lambda k=6: FakeChain())
    from api import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ask_valid_question_returns_the_chain_result(client):
    r = client.post("/ask", json={"question": "What is the minimum attendance requirement?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "75%"
    assert body["found_in_document"] is True
    assert body["sources"] == [{"document": "Academic Rules and Regulations 2024", "page": 5}]


def test_ask_rejects_empty_question(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ask_rejects_oversized_question(client):
    assert client.post("/ask", json={"question": "a" * 501}).status_code == 422


def test_ask_rejects_missing_question_field(client):
    assert client.post("/ask", json={}).status_code == 422


def test_rate_limit_blocks_after_the_daily_cap(client, monkeypatch):
    monkeypatch.setattr("api.DAILY_LIMIT_PER_IP", 2)
    q = {"question": "What is the minimum attendance requirement?"}
    assert client.post("/ask", json=q).status_code == 200
    assert client.post("/ask", json=q).status_code == 200
    r = client.post("/ask", json=q)
    assert r.status_code == 429
    assert "limit" in r.json()["detail"].lower()
