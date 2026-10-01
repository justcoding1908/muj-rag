"""Retrieval sanity checks — no Groq calls, just the embedding model + Chroma, so these
are free and fast on every push. They assume `python ingest.py` has already built
chroma_db/ from data/ + ocr_cache/ (the CI workflow does this before running pytest).

Scores are asserted as ranges, not exact floats — the embedding model can produce tiny
floating-point differences across hardware, so pinning exact values would be flaky.
"""
import os
import pytest
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from rag_chain import REFUSAL_THRESHOLD

CHROMA_DIR = "chroma_db"


@pytest.fixture(scope="module")
def vectorstore():
    if not os.path.isdir(CHROMA_DIR) or not os.listdir(CHROMA_DIR):
        pytest.skip(f"{CHROMA_DIR}/ not built — run `python ingest.py` first")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)


def top1(vectorstore, question):
    doc, score = vectorstore.similarity_search_with_score(question, k=1)[0]
    return doc, score


@pytest.mark.parametrize("question, expected_doc, expected_page", [
    ("What is the minimum attendance percentage required to be permitted to write the end-semester exam?",
     "Academic Rules and Regulations 2024", 5),
    ("How many White DoTs does a student earn for six months of good conduct after a DoT order?",
     "DoT Policy 2025-26", 7),
    ("Which plagiarism detection software does the policy mention?",
     "Plagiarism Policy 2016", 2),
])
def test_known_facts_retrieve_the_right_page(vectorstore, question, expected_doc, expected_page):
    doc, score = top1(vectorstore, question)
    assert doc.metadata["doc_name"] == expected_doc
    assert doc.metadata["page"] + 1 == expected_page
    assert score < REFUSAL_THRESHOLD  # a real, on-topic question must never be refused by the threshold


@pytest.mark.parametrize("question", [
    "What is a good recipe for chocolate cake?",
    "What is the phone number of the anti-ragging helpline?",
])
def test_blatantly_off_topic_questions_score_above_threshold(vectorstore, question):
    # These are the two questions the refusal threshold is specifically there to catch
    # before the LLM is ever called (see the REFUSAL_THRESHOLD comment in rag_chain.py).
    _, score = top1(vectorstore, question)
    assert score > REFUSAL_THRESHOLD
