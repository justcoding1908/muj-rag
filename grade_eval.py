import json

with open("eval_results_baseline.json", encoding="utf-8") as f:
    results = json.load(f)

correct, cite_correct, cite_checkable = 0, 0, 0
by_category = {}

for item in results:
    print(f"\n[{item['id']}] ({item['category']}) {item['question']}")
    print(f"  Expected: {item['expected_answer']}  | Got: {item['actual_answer']}")
    ok = input("  Answer correct? (y/n): ").strip().lower() == "y"
    item["correct"] = ok
    correct += ok
    by_category.setdefault(item["category"], []).append(ok)

    if item["category"] != "unanswerable":
        got = item.get("actual_sources", item.get("actual_pages"))  # older result files only have page numbers
        print(f"  Expected: {item.get('source_doc')}, p.{item.get('source_page')}  | Got: {got}")
        cite_ok = input("  Citation correct? (y/n): ").strip().lower() == "y"
        item["citation_correct"] = cite_ok
        cite_checkable += 1
        cite_correct += cite_ok

print(f"\nAnswer accuracy:   {correct}/{len(results)} = {correct/len(results)*100:.1f}%")
if cite_checkable:
    print(f"Citation accuracy: {cite_correct}/{cite_checkable} = {cite_correct/cite_checkable*100:.1f}%")
for cat, vals in by_category.items():
    print(f"  {cat}: {sum(vals)}/{len(vals)} = {sum(vals)/len(vals)*100:.1f}%")

with open("eval_results_baseline_graded.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
