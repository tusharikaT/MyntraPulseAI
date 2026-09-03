import os
import sys
import sqlite3
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

# Ensure data directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), "../data/chroma"), exist_ok=True)

def extract_and_chunk():
    """
    Extracts all classified records from SQLite.
    Since feedback data is usually short (tweets, reviews), the 'chunk' is often just the full text.
    However, we format the chunk nicely by injecting the metadata into the text itself 
    so the embedding model captures the context (e.g., journey stage, intent).
    """
    conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../data/db/discovery.db"))
    
    # We want to join feedback_records with classifications so we have rich context
    query = '''
    SELECT 
        f.record_id, 
        f.cleaned_text, 
        f.source_type, 
        f.original_url as url,
        c.journey_stage,
        c.wishlist_intent,
        c.barrier_labels
    FROM feedback_records f
    JOIN classifications c ON f.record_id = c.record_id
    '''
    df = pd.read_sql(query, conn)
    conn.close()
    
    chunks = []
    
    for _, row in df.iterrows():
        # Create a rich semantic chunk
        # Instead of just embedding the raw text, we embed a structured paragraph
        # This helps the RAG model significantly.
        barrier_labels = row['barrier_labels']
        if not barrier_labels or barrier_labels == '[]':
            barrier_str = "None"
        else:
            barrier_str = str(barrier_labels).replace('[', '').replace(']', '').replace("'", "")
            
        rich_chunk = (
            f"User Feedback (Source: {row['source_type']}): {row['cleaned_text']}\n"
            f"Context: The user is in the '{row['journey_stage']}' stage. "
            f"Their primary intent is '{row['wishlist_intent']}'. "
            f"Key barriers experienced: {barrier_str}."
        )
        
        chunks.append({
            "id": row['record_id'],
            "text": rich_chunk,
            "metadata": {
                "source_type": row['source_type'] or "unknown",
                "url": row['url'] or "",
                "journey_stage": row['journey_stage'] or "unknown",
                "intent": row['wishlist_intent'] or "unknown"
            }
        })
        
    return chunks

def preview_chunks():
    print("Extracting and creating semantic chunks from database...")
    chunks = extract_and_chunk()
    print(f"Successfully generated {len(chunks)} chunks.")
    
    preview_file = r'C:\Users\DELL\.gemini\antigravity-ide\brain\a676e9fa-60a5-41a6-b80d-f9f0e76a71b2\chunk_preview.md'
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write("# Chunk Preview\n\n")
        f.write(f"Successfully generated {len(chunks)} chunks from the database.\n\n")
        f.write("## First 3 Chunks\n\n")
        for i, c in enumerate(chunks[:3]):
            f.write(f"### [Chunk {i+1}] ID: {c['id']}\n")
            f.write(f"**TEXT:**\n```text\n{c['text']}\n```\n")
            f.write(f"**METADATA:**\n```json\n{c['metadata']}\n```\n\n")
            
    print("Preview written to chunk_preview.md")
    print("PAUSING execution as requested.")

def embed_and_upsert():
    print("Initializing local ChromaDB and SentenceTransformer...")
    # Using the fast, lightweight BGE small model which is SOTA for short queries
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "../data/chroma"))
    collection = client.get_or_create_collection(name="feedback_collection")
    
    chunks = extract_and_chunk()
    
    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    
    print(f"Generating embeddings for {len(texts)} chunks (this runs locally on CPU and may take a minute)...")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    
    print("Upserting into ChromaDB...")
    # Batch upsert to avoid memory spikes
    batch_size = 200
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            documents=texts[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size]
        )
        
    print(f"Successfully indexed {len(ids)} chunks into ChromaDB!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--upsert":
        embed_and_upsert()
    else:
        preview_chunks()
