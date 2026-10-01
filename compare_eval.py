import argparse
import json


def score(path):
    with open(path, encoding="utf-8") as f:
        results = json.load(f)

    citable = [r for r in results if r["category"] != "unanswerable"]
    cite_correct = sum(1 for r in citable if r["page_match"])
    errors = sum(1 for r in results if r["actual_found"] is None)

    unanswerable = [r for r in results if r["category"] == "unanswerable"]
    refusal_correct = sum(1 for r in unanswerable if r["actual_found"] is False)

    return {
        "citation_accuracy": cite_correct / len(citable) if citable else None,
        "citation_n": f"{cite_correct}/{len(citable)}",
        "refusal_accuracy": refusal_correct / len(unanswerable) if unanswerable else None,
        "refusal_n": f"{refusal_correct}/{len(unanswerable)}",
        "errors": errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", help="eval result JSON files to compare")
    args = parser.parse_args()

    for path in args.files:
        s = score(path)
        print(f"\n{path}")
        print(f"  Citation accuracy (right page cited): {s['citation_n']} = {s['citation_accuracy']*100:.1f}%")
        print(f"  Refusal accuracy (correctly said 'not in document'): {s['refusal_n']} = {s['refusal_accuracy']*100:.1f}%")
        if s["errors"]:
            print(f"  Errors (excluded from scoring): {s['errors']}")
