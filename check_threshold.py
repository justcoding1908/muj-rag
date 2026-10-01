import json
from collections import defaultdict
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="chroma_db", embedding_function=embeddings)

with open("eval_set.json", encoding="utf-8") as f:
    eval_set = json.load(f)

by_category = defaultdict(list)

print(f"{'ID':<4} {'Category':<16} {'Top score':<10} Question")
for item in eval_set:
    results = vectorstore.similarity_search_with_score(item["question"], k=1)
    score = results[0][1] if results else float("inf")
    by_category[item["category"]].append(score)
    print(f"{item['id']:<4} {item['category']:<16} {score:<10.4f} {item['question'][:55]}")

print("\n--- Summary by category (lower score = more similar) ---")
for cat, scores in by_category.items():
    print(f"{cat:<16} min={min(scores):.4f}  max={max(scores):.4f}  avg={sum(scores)/len(scores):.4f}")
