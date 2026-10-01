# MUJ Policy Assistant

A RAG (retrieval-augmented generation) API that answers questions about Manipal
University Jaipur's official policy documents — academic rules, attendance monitoring,
the DoT (discipline) policy, the code of ethics and conduct, and the plagiarism policy —
citing the exact document and page each answer came from, and refusing to answer
questions those documents don't cover.

## How it works

1. The 5 policy PDFs in `data/` are split into chunks and embedded (`ingest.py`), then
   stored in a local Chroma vector database.
2. A question is embedded the same way and compared against every chunk. If even the
   closest chunk is too dissimilar, the question is refused before any LLM call is made
   (`REFUSAL_THRESHOLD` in `rag_chain.py`) — this is a deliberate hard backstop, not just
   the model's judgment.
3. Otherwise, the closest chunks are sent to the LLM (Groq, `openai/gpt-oss-20b`), which
   must answer only from that context and cite the document + page it used.
4. A code-level check (`validate_grounding`) then verifies every citation the model gives
   actually matches a chunk it was shown — if it claims an answer is "found" but can't
   back that up with a real citation, the claim is overridden to a refusal. This exists
   because prompt wording alone wasn't enough: a test question embedded an instruction
   telling the model to fabricate an answer, and it complied until this check was added.

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # or: source venv/bin/activate on Linux/macOS
pip install -r requirements.txt

cp .env.example .env           # then fill in GROQ_API_KEY
```

You also need Redis running locally (used as the LLM response cache and the API's
rate-limit counter):

```bash
docker run -d --name muj-redis -p 6379:6379 redis
```

Build the vector database from the PDFs in `data/` (scanned pages reuse the OCR text
already cached in `ocr_cache/`, so this is fast):

```bash
python ingest.py
```

## Running it

**Command line:**
```bash
python ask.py
```

**API server:**
```bash
uvicorn api:app --reload
```
Then `POST /ask` with `{"question": "..."}`, or `GET /health` to check it's up.

## Testing

```bash
pytest tests/
```

These are free — no Groq calls. They check retrieval, the citation-grounding safety net,
and the API's request validation and rate limiting.

The full 62-question eval (`run_eval.py`) does call Groq and costs real tokens against
the daily quota, so it isn't run on every push. Run it manually:
```bash
python run_eval.py --output eval_results_full.json
python check_eval_results.py eval_results_full.json   # pass/fail gate
```
Or trigger it from GitHub Actions (Actions tab → Tests → Run workflow → check
"run_full_eval"). See `.github/workflows/test.yml`.

`check_eval_results.py` only checks what's automatable: whether citations point to the
right document/page, and whether out-of-scope questions were correctly refused. It does
not grade whether the answer's wording is actually correct — for that, `grade_eval.py`
walks through each result and asks a human.

## Project layout

| File | Purpose |
|---|---|
| `ingest.py` | Loads the PDFs in `data/`, OCRs scanned pages, chunks, embeds, stores in Chroma |
| `pdf_loader.py` | PDF text extraction + OCR fallback, with on-disk caching |
| `rag_chain.py` | The core pipeline: retrieval, refusal threshold, prompt, citation grounding |
| `api.py` | FastAPI wrapper — `/ask`, `/health`, rate limiting |
| `ask.py` | Command-line entry point |
| `run_eval.py` / `grade_eval.py` / `compare_eval.py` | Eval harness |
| `eval_set.json` | The 62-question eval set (factual, paraphrased, cross-reference, unanswerable) |
| `injection_tests.json` / `run_injection_tests.py` | Prompt-injection test set |
| `tests/` | Automated pytest suite (no LLM calls) |
