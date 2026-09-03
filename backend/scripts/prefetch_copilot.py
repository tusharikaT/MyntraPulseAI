import os
import sys
import json

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.copilot import query_copilot

questions = [
    "Why do users add fashion products to their wishlist?",
    "What prevents wishlisted products from eventually being purchased?",
    "What uncertainties remain after users have identified a product they like?",
    "What causes users to postpone a purchase?",
    "How do users compare multiple shortlisted products?",
    "What information do users seek outside Myntra/AJIO before purchasing?",
    "What role do fit, size, styling, price, reviews, occasion and social validation play?",
    "When do users use the wishlist as genuine purchase intent versus simply as a bookmarking mechanism?",
    "How do these behaviors differ across user segments?",
    "What unmet needs emerge consistently across user conversations?",
    "Which new wishlist features would most effectively resolve user friction?",
    "How can Myntra increase the conversion rate of saved items during major sale events?"
]

output_file = os.path.join(os.path.dirname(__file__), '../data/prefetched_copilot.json')
results = {}

print("Starting prefetch for 12 default questions...")
for idx, q in enumerate(questions):
    print(f"[{idx+1}/12] Querying: {q}")
    res = query_copilot(q, top_k=5) # use top_k=5 to speed things up
    results[q] = res
    print(f"   -> Done.")

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f"Successfully saved {len(results)} queries to {output_file}")
