import sys
sys.stdout.reconfigure(encoding="utf-8")
import time
from dotenv import load_dotenv
load_dotenv()

from rag_chain import build_chain

chain = build_chain(k=6)
question = "What is the maximum duration allowed to complete an academic program"

start = time.time()
result = chain.invoke(question)
elapsed = time.time() - start

print(f"Answer:  {result.answer}")
print("Sources: " + ("; ".join(f"{s.document}, p.{s.page}" for s in result.sources) or "none"))
print(f"Found:   {result.found_in_document}")
print(f"Time:    {elapsed:.2f}s")
