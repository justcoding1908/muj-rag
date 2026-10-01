"""Pass/fail gate for CI's full-eval job: load eval_results JSON (from run_eval.py) and
fail (non-zero exit) if it's worse than what the project has already demonstrated.

This only checks what's automatable without a human: citation correctness (document +
page matched what we expect) and refusal correctness (out-of-scope questions were
refused). It does NOT check free-text answer wording — that still needs a human with
grade_eval.py. Thresholds are set from the last fully-graded run (eval_results_62_v2.json,
2026-09-27): 50/52 citations, 10/10 refusals, 0 errors.
"""
import argparse
import json
import sys

MIN_CITATION_ACCURACY = 0.90  # last known: 50/52 = 96.2%
MIN_REFUSAL_ACCURACY = 1.0    # last known: 10/10 = 100%


def check(path):
    with open(path, encoding="utf-8") as f:
        results = json.load(f)

    errors = [r for r in results if r["actual_found"] is None]

    citable = [r for r in results if r["category"] != "unanswerable"]
    cite_correct = sum(1 for r in citable if r["page_match"])
    citation_accuracy = cite_correct / len(citable) if citable else None

    unanswerable = [r for r in results if r["category"] == "unanswerable"]
    refusal_correct = sum(1 for r in unanswerable if r["actual_found"] is False)
    refusal_accuracy = refusal_correct / len(unanswerable) if unanswerable else None

    print(f"Loaded {len(results)} results from {path}")
    print(f"  Errors (questions that failed to answer at all): {len(errors)}")
    if citation_accuracy is not None:
        print(f"  Citation accuracy: {cite_correct}/{len(citable)} = {citation_accuracy * 100:.1f}% (min {MIN_CITATION_ACCURACY * 100:.0f}%)")
    if refusal_accuracy is not None:
        print(f"  Refusal accuracy:  {refusal_correct}/{len(unanswerable)} = {refusal_accuracy * 100:.1f}% (min {MIN_REFUSAL_ACCURACY * 100:.0f}%)")

    failures = []
    if errors:
        failures.append(f"{len(errors)} question(s) errored out: {[r['id'] for r in errors]}")
    if citation_accuracy is not None and citation_accuracy < MIN_CITATION_ACCURACY:
        failures.append(f"citation accuracy {citation_accuracy * 100:.1f}% is below the {MIN_CITATION_ACCURACY * 100:.0f}% floor")
    if refusal_accuracy is not None and refusal_accuracy < MIN_REFUSAL_ACCURACY:
        failures.append(f"refusal accuracy {refusal_accuracy * 100:.1f}% is below the {MIN_REFUSAL_ACCURACY * 100:.0f}% floor")

    if failures:
        print("\nFAIL:")
        for f_ in failures:
            print(f"  - {f_}")
        return False

    print("\nPASS")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("results_file", nargs="?", default="eval_results_full.json")
    args = parser.parse_args()
    sys.exit(0 if check(args.results_file) else 1)
