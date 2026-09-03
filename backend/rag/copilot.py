import os
import sys
import sqlite3
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

def get_groq_client():
    keys = [
        os.environ.get(f"GROQ_API_KEY_{i}") if i > 1 else os.environ.get("GROQ_API_KEY") 
        for i in range(1, 12)
    ]
    for key in keys:
        if key:
            try:
                return Groq(api_key=key)
            except Exception:
                continue
    return None

def get_dataset_summary():
    db_path = os.path.join(os.path.dirname(__file__), "../data/db/discovery.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM feedback_records WHERE is_relevant = 1")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT source_type, COUNT(*) FROM feedback_records WHERE is_relevant = 1 GROUP BY source_type")
        source_mix = dict(cursor.fetchall())
        conn.close()
        return {"total_records": total, "source_mix": source_mix}
    except:
        return {"total_records": 0, "source_mix": {}}

def query_copilot(question: str, top_k: int = 10, filters: dict = None) -> dict:
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    query_embedding = model.encode(question).tolist()
    
    client = chromadb.PersistentClient(path=os.path.join(os.path.dirname(__file__), "../data/chroma"))
    collection = client.get_collection(name="feedback_collection")
    
    where_clause = {}
    if filters:
        # Chroma where clause mapping
        if filters.get("platform"):
            where_clause["platform"] = filters["platform"]
        # Can expand filters here if needed
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_clause if where_clause else None
    )
    
    documents = results['documents'][0] if results['documents'] else []
    metadatas = results['metadatas'][0] if results['metadatas'] else []
    ids = results['ids'][0] if results['ids'] else []
    
    if not documents:
        return {
            "answer": "I could not find any relevant feedback in the database to answer your question.",
            "sources": [],
            "dataset_summary": get_dataset_summary(),
            "suggested_followups": []
        }
    
    context_str = ""
    sources_list = []
    for i in range(len(documents)):
        context_str += f"\n--- Record {i+1} ---\n"
        context_str += f"{documents[i]}\n"
        context_str += f"Source URL: {metadatas[i].get('url', 'N/A')}\n"
        
        sources_list.append({
            "record_id": ids[i],
            "quote": documents[i][:150] + "...",  # Preview quote
            "original_url": metadatas[i].get('url', ''),
            "platform": metadatas[i].get('platform', 'unknown'),
            "source_type": metadatas[i].get('source_type', 'unknown'),
            "rating": None
        })
    
    groq_client = get_groq_client()
    system_prompt = """You are the Myntra Discovery Copilot, an AI assistant for Product Managers investigating Wishlist-to-Purchase conversion barriers.
Your job is to answer questions based *strictly* on the user feedback records provided in the context.
Rules for Evidence vs Inference:
1. ONLY use the provided context to answer the question. Do NOT hallucinate insights or infer outside of the text.
2. If the context does not contain the answer, you must state: "I don't have enough data to answer that based on the current records."
3. When making a claim, you MUST explicitly quote the user text from the context and cite the source using the [Record X] format, e.g. "Users note: 'sizing is confusing' [Record 1]."
4. Structure your answers analytically around core friction groupings (Price, Fit, Quality, Comparison) if relevant.
5. Be concise and professional. Do not provide generic advice.
"""
    user_prompt = f"Context Data:\n{context_str}\n\nQuestion: {question}"

    answer = ""
    try:
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        answer = completion.choices[0].message.content
    except Exception as e:
        answer = f"Error communicating with AI model: {e}"

    return {
        "answer": answer,
        "sources": sources_list,
        "dataset_summary": get_dataset_summary(),
        "suggested_followups": [
            "What are the top barriers to conversion?",
            "Are there differences between iOS and Android users?",
            "How does price uncertainty impact the wishlist?"
        ]
    }
