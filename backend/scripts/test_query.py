import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "../data/db/discovery.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

base_query = """
    FROM feedback_records r
    LEFT JOIN classifications c ON r.record_id = c.record_id
    WHERE r.is_relevant = 1
"""

data_query = f"""
    SELECT 
        r.record_id,
        r.date_published,
        r.date_scraped,
        r.platform,
        r.source_type,
        r.raw_text,
        c.wishlist_relevance,
        c.wishlist_intent,
        c.barrier_labels,
        c.journey_stage
    {base_query}
    ORDER BY COALESCE(r.date_published, r.date_scraped) DESC
    LIMIT ? OFFSET ?
"""

cursor.execute(data_query, [10, 0])
rows = cursor.fetchall()
print(f"Number of rows: {len(rows)}")

if len(rows) > 0:
    print(dict(rows[0]))
