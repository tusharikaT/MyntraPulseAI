"""
ETL Pipeline Orchestrator (Phase 3).
Reads JSON from data/raw/, filters, cleans, and upserts to SQLite.
"""
import sys
import os
import glob
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.dialects.sqlite import insert

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.filters import detect_language, is_relevant, clean_text
from config.scraper_config import KEYWORD_FILTERS
from data.db.models import SessionLocal, SyncRun, StageLog, FeedbackRecord

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

def run_etl():
    """Execute the full 5-stage ETL pipeline."""
    print("Starting ETL Pipeline...")
    sync_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)
    
    db = SessionLocal()
    
    # Create SyncRun record
    sync_run = SyncRun(
        sync_id=sync_id,
        started_at=start_time,
        status="running"
    )
    db.add(sync_run)
    db.commit()

    # Metrics trackers
    metrics = {
        "raw_total": 0,
        "english_total": 0,
        "relevant_total": 0,
        "cleaned_total": 0,
        "inserted_total": 0
    }
    
    json_files = glob.glob(os.path.join(RAW_DIR, "*.json"))
    print(f"Found {len(json_files)} raw JSON files.")
    
    synthetic_records = []
    real_records = []
    
    for filepath in json_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            raw_records = data.get("records", [])
            source_type = data.get("scraper", "unknown")
            
            for raw in raw_records:
                if "_synthetic_" in filepath or raw.get("metadata", {}).get("is_synthetic"):
                    synthetic_records.append((raw, source_type))
                else:
                    real_records.append((raw, source_type))
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    import random
    # Optional deterministic seed for reproducibility
    random.seed(42)
    random.shuffle(real_records)
    
    # We want exactly 268 real records to complement the 1068 synthetic ones
    sampled_real = real_records[:268]
    combined_records = synthetic_records + sampled_real
    
    print(f"Ingesting {len(synthetic_records)} synthetic and {len(sampled_real)} real records.")
    
    records_to_insert = []
    
    for raw, source_type in combined_records:
        try:
            metrics["raw_total"] += 1
            
            # Extract fields
            record_id = raw.get("record_id")
            platform = raw.get("platform", "Unknown")
            raw_text = raw.get("raw_text", "")
            
            if not raw_text:
                continue
                
            # Stage 2: Language Filter
            lang = detect_language(raw_text)
            if lang != 'en':
                continue
            metrics["english_total"] += 1
            
            # Stage 3: Relevance Filter
            relevant = is_relevant(raw_text, KEYWORD_FILTERS)
            if not relevant:
                continue
            metrics["relevant_total"] += 1
            
            # Stage 4: Clean & Normalise
            cleaned = clean_text(raw_text)
            if not cleaned:
                continue
            metrics["cleaned_total"] += 1
            
            # Prepare for DB
            # Parse datetime if valid
            dt_pub = None
            if raw.get("date_published"):
                try:
                    # naive attempt, if it fails we just leave None
                    if "ago" not in raw["date_published"]:
                         dt_pub = datetime.fromisoformat(raw["date_published"].replace('Z', '+00:00'))
                except:
                    pass
                    
            dt_scrape = datetime.now(timezone.utc)
            if raw.get("date_scraped"):
                try:
                    dt_scrape = datetime.fromisoformat(raw["date_scraped"].replace('Z', '+00:00'))
                except:
                    pass
            
            records_to_insert.append({
                "record_id": record_id,
                "sync_id": sync_id,
                "source_type": raw.get("source_type", source_type),
                "platform": platform,
                "original_url": raw.get("original_url"),
                "date_published": dt_pub,
                "date_scraped": dt_scrape,
                "raw_text": raw_text,
                "cleaned_text": cleaned,
                "language": "en",
                "rating": raw.get("rating"),
                "engagement": raw.get("engagement"),
                "metadata_": raw.get("metadata", {}),
                "is_relevant": True
            })
            
        except Exception as e:
            print(f"Error processing a record: {e}")

    # Stage 5: DB Load (Upsert / Ignore duplicates)
    if records_to_insert:
        print(f"Attempting to upsert {len(records_to_insert)} records to SQLite...")
        
        # We chunk inserts to avoid SQLite parameter limits
        chunk_size = 500
        inserted_count = 0
        
        for i in range(0, len(records_to_insert), chunk_size):
            chunk = records_to_insert[i:i + chunk_size]
            
            # Upsert logic (INSERT OR IGNORE)
            stmt = insert(FeedbackRecord).values(chunk)
            stmt = stmt.on_conflict_do_nothing(index_elements=['record_id'])
            
            result = db.execute(stmt)
            inserted_count += result.rowcount
            
        metrics["inserted_total"] = inserted_count
        db.commit()
    
    # Save Stage Logs
    logs = [
        StageLog(sync_id=sync_id, stage="raw", count=metrics["raw_total"]),
        StageLog(sync_id=sync_id, stage="english", count=metrics["english_total"]),
        StageLog(sync_id=sync_id, stage="relevant", count=metrics["relevant_total"]),
        StageLog(sync_id=sync_id, stage="cleaned", count=metrics["cleaned_total"]),
        StageLog(sync_id=sync_id, stage="inserted", count=metrics["inserted_total"])
    ]
    db.add_all(logs)
    
    # Finish SyncRun
    sync_run.completed_at = datetime.now(timezone.utc)
    sync_run.status = "success"
    sync_run.summary = metrics
    db.commit()
    db.close()
    
    print("\n--- ETL Run Summary ---")
    print(f"Raw Input:       {metrics['raw_total']}")
    print(f"Passed English:  {metrics['english_total']}")
    print(f"Passed Relevant: {metrics['relevant_total']}")
    print(f"Cleaned Text:    {metrics['cleaned_total']}")
    print(f"New Inserted:    {metrics['inserted_total']}")
    print("-----------------------")
    print(f"Sync complete. Sync ID: {sync_id}")

if __name__ == "__main__":
    run_etl()
