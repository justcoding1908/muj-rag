"""Regression tests for the prompt-injection fix (validate_grounding in rag_chain.py).

No Groq calls here — these construct fake RAGAnswer/document objects directly, so they
run free and fast on every push. They exist because the prompt alone was proven not
reliable enough: a test question got the model to fabricate an answer and mark it
"found" via an instruction embedded in the question itself (see injection_tests.json,
test inj-5). validate_grounding is the code-level backstop for that; these tests make
sure nobody can quietly remove or weaken it later.
"""
from langchain_core.documents import Document
from rag_chain import RAGAnswer, Source, REFUSAL_ANSWER, validate_grounding


def _doc(name, page):
    return Document(page_content="irrelevant", metadata={"doc_name": name, "page": page - 1})


RETRIEVED_DOCS = [_doc("DoT Policy 2025-26", 7), _doc("Attendance Monitoring Policy", 5)]


def test_real_citation_is_kept():
    result = RAGAnswer(
        answer="Two White DoTs.",
        sources=[Source(document="DoT Policy 2025-26", page=7)],
        found_in_document=True,
    )
    out = validate_grounding(result, RETRIEVED_DOCS)
    assert out.found_in_document is True
    assert out.answer == "Two White DoTs."
    assert [(s.document, s.page) for s in out.sources] == [("DoT Policy 2025-26", 7)]


def test_fabricated_citation_is_dropped_but_real_one_survives():
    result = RAGAnswer(
        answer="75% attendance.",
        sources=[
            Source(document="Attendance Monitoring Policy", page=5),
            Source(document="Confidential Internal Memo", page=99),  # never retrieved
        ],
        found_in_document=True,
    )
    out = validate_grounding(result, RETRIEVED_DOCS)
    assert [(s.document, s.page) for s in out.sources] == [("Attendance Monitoring Policy", 5)]
    assert out.found_in_document is True  # one real source survives, so the claim stands


def test_found_true_with_no_real_sources_is_overridden_to_refusal():
    """The exact shape of the inj-5 attack: found_in_document=True but nothing backing it up."""
    result = RAGAnswer(
        answer="The minimum GPA required to avoid academic probation is 5.0.",
        sources=[],
        found_in_document=True,
    )
    out = validate_grounding(result, RETRIEVED_DOCS)
    assert out.found_in_document is False
    assert out.answer == REFUSAL_ANSWER
    assert out.sources == []


def test_found_true_with_only_fabricated_sources_is_overridden_to_refusal():
    result = RAGAnswer(
        answer="The minimum GPA required to avoid academic probation is 5.0.",
        sources=[Source(document="Confidential Internal Memo", page=99)],
        found_in_document=True,
    )
    out = validate_grounding(result, RETRIEVED_DOCS)
    assert out.found_in_document is False
    assert out.answer == REFUSAL_ANSWER


def test_correct_refusal_is_left_alone():
    """found_in_document=False with no sources is the normal, correct refusal shape — must not be touched."""
    result = RAGAnswer(answer=REFUSAL_ANSWER, sources=[], found_in_document=False)
    out = validate_grounding(result, RETRIEVED_DOCS)
    assert out.found_in_document is False
    assert out.answer == REFUSAL_ANSWER
