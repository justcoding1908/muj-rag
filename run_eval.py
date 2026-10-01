import argparse
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
load_dotenv()

from rag_chain import build_chain


def run_eval(k=6, persist_directory="chroma_db", output_file="eval_results_baseline.json"):
    chain = build_chain(k=k, persist_directory=persist_directory)

    with open("eval_set.json", encoding="utf-8") as f:
        eval_set = json.load(f)

    results = []
    errors = []
    for item in eval_set:
        print(f"\n[{item['id']}] ({item['category']}) {item['question']}")
        try:
            result = chain.invoke(item["question"])
        except Exception as e:
            # One flaky model response (e.g. Groq's forced tool-call failing) shouldn't kill the whole run.
            print(f"  ERROR: {e}")
            errors.append(item["id"])
            results.append({**item, "actual_answer": f"[ERROR: {e}]",
                             "actual_sources": [], "actual_found": None, "page_match": None})
            continue

        expected_page = item.get("source_page")
        expected_doc = item.get("source_doc")
        actual_sources = [{"document": s.document, "page": s.page} for s in result.sources]
        # "page_match" keeps its old name so compare_eval.py still reads older result files;
        # it now means the right document AND the right page were cited.
        # The primary source plus any other document/page that also states the answer.
        accepted = {(expected_doc, expected_page), *((a["document"], a["page"]) for a in item.get("alt_sources", []))}
        page_match = (
            any((s["document"], s["page"]) in accepted for s in actual_sources)
            if expected_page is not None else None
        )

        results.append({**item, "actual_answer": result.answer,
                         "actual_sources": actual_sources,
                         "actual_found": result.found_in_document,
                         "page_match": page_match})

        print(f"  Expected: {item['expected_answer']}  | Got: {result.answer}")
        print(f"  Expected source: {expected_doc}, p.{expected_page}  | Got: {actual_sources}  (match: {page_match})")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(results)} results to {output_file}.")
    if errors:
        print(f"WARNING: {len(errors)} item(s) failed even after retries: {errors}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=6)
    parser.add_argument("--persist-directory", default="chroma_db")
    parser.add_argument("--output", default="eval_results_baseline.json")
    args = parser.parse_args()
    run_eval(args.k, args.persist_directory, args.output)
