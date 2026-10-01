import sys
import os
import json
sys.stdout.reconfigure(encoding="utf-8")
from dotenv import load_dotenv
load_dotenv()

from rag_chain import build_chain


def run_injection_tests(output_file="injection_results.json"):
    with open("injection_tests.json", encoding="utf-8") as f:
        tests = json.load(f)

    # Resume support: memory on this machine is tight, so a run can get killed partway.
    # Skip tests already answered in a previous (partial) run of this file.
    done = {}
    if os.path.exists(output_file):
        with open(output_file, encoding="utf-8") as f:
            done = {r["id"]: r for r in json.load(f)}

    pending = [t for t in tests if t["id"] not in done]
    if not pending:
        print("All tests already have results.")
        return

    chain = build_chain(k=6)
    results = [done[t["id"]] for t in tests if t["id"] in done]

    for t in pending:
        print(f"\n[{t['id']}] ({t['type']}) {t['question'][:90]}")
        try:
            result = chain.invoke(t["question"])
            answer, sources, found = result.answer, [f"{s.document} p.{s.page}" for s in result.sources], result.found_in_document
        except Exception as e:
            answer, sources, found = f"[ERROR: {e}]", [], None

        record = {**t, "actual_answer": answer, "actual_sources": sources, "actual_found": found}
        results.append(record)
        print(f"  Answer: {answer}")
        print(f"  Sources: {sources}  Found: {found}")

        # Save after every single question so a kill mid-run loses at most one answer.
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} results to {output_file}.")


if __name__ == "__main__":
    run_injection_tests()
