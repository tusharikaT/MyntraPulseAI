"""
AI Classification Engine using Gemini and Groq.
Iterates over unclassified relevant records and applies the taxonomy.
Uses multi-threading to classify records in parallel using multiple API keys.
"""
import os
import sys
import time
import json
import random
import traceback
import concurrent.futures
from datetime import datetime, timezone
from dotenv import load_dotenv

BARRIER_FAMILY_MAP = {
    "fit": "Fit & sizing",
    "size_chart": "Fit & sizing",
    "quality": "Quality & material",
    "authenticity": "Quality & material",
    "reviews_info_gaps": "Information gaps",
    "out_of_stock": "Availability",
    "price_value_uncertainty": "Price & value",
    "clutter": "Wishlist UX",
    "rediscovery": "Wishlist UX",
    "comparison_difficulty": "Comparison difficulty",
    "bookmarking_only": "Low intent",
    "delivery": "Logistics",
    "returns": "Logistics",
    "checkout": "Logistics",
    "payment": "Logistics"
}

JOURNEY_STAGE_MAP = {
    "browse": "Pre-product",
    "pdp": "Product evaluation",
    "comparison": "Product evaluation",
    "wishlist_add": "Shortlist / intent",
    "wishlist_revisit": "Shortlist / intent",
    "add_to_bag": "Purchase",
    "checkout": "Purchase",
    "payment": "Purchase",
    "order": "Purchase",
    "delivery": "Post-purchase",
    "return_exchange": "Post-purchase"
}

from google import genai
from google.genai import types
from groq import Groq
from pydantic import BaseModel, Field
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.db.models import SessionLocal, FeedbackRecord, Classification

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Load all 15 Groq API keys
ALL_GROQ_KEYS = [
    os.environ.get(f"GROQ_API_KEY_{i}") if i > 1 else os.environ.get("GROQ_API_KEY") 
    for i in range(1, 16)
]
ALL_GROQ_KEYS = [k for k in ALL_GROQ_KEYS if k] # Filter empty ones

class ClassificationOutput(BaseModel):
    wishlist_relevance: str = Field(
        description="One of: wishlist_related, shopping_generic, unknown"
    )
    journey_stage: str = Field(
        description="One of: browse, pdp, wishlist_add, wishlist_revisit, comparison, add_to_bag, checkout, payment, order, delivery, return_exchange, unknown"
    )
    wishlist_intent: str = Field(
        description="One of: immediate_purchase, genuine_consideration, comparison, availability_waiting, occasion_waiting, gift_planning, price_monitoring, styling_inspiration, general_bookmarking, unknown. MUST be 'unknown' if wishlist_relevance is not 'wishlist_related'."
    )
    barrier_labels: List[str] = Field(
        description="Subset of: clutter, rediscovery, out_of_stock, fit, size_chart, quality, authenticity, reviews_info_gaps, comparison_difficulty, styling, occasion_suitability, social_validation, delivery, returns, checkout, payment, notification_fatigue, low_urgency, bookmarking_only, price_value_uncertainty, other"
    )
    purchase_outcome: str = Field(
        description="One of: purchased, postponed, abandoned, returned, unknown, not_applicable"
    )
    external_research: List[str] = Field(
        description="Subset of: youtube, instagram, reddit, google, brand_site, other_ecommerce, offline_store, friends_family, influencer, fashion_community, none, unknown"
    )
    segment_tags: List[str] = Field(default_factory=list)
    signal_families: List[str] = Field(default_factory=list)

def derive_segments_and_signals(output: ClassificationOutput) -> ClassificationOutput:
    barriers = output.barrier_labels or []
    intent = output.wishlist_intent or "unknown"
    outcome = output.purchase_outcome or "unknown"
    
    segments = []
    if intent in ["immediate_purchase", "genuine_consideration"] and outcome in ["purchased", "returned"]:
        segments.append("high_intent")
    if "fit" in barriers or "size_chart" in barriers:
        segments.append("fit_sensitive")
    if "price_value_uncertainty" in barriers:
        segments.append("value_conscious")
    if intent in ["styling_inspiration", "general_bookmarking"]:
        segments.append("inspiration_bookmarker")
    if intent == "occasion_waiting":
        segments.append("occasion_shopper")
    if "reviews_info_gaps" in barriers:
        segments.append("review_dependent")
    if "comparison_difficulty" in barriers or intent == "comparison":
        segments.append("comparison_shopper")
        
    output.segment_tags = list(set(segments))
    
    signals = []
    if intent != "unknown":
        signals.append("1-wishlist_intent")
    if barriers:
        signals.append("2-purchase_barriers")
    if any(b in ["clutter", "rediscovery", "comparison_difficulty", "bookmarking_only"] for b in barriers):
        signals.append("3-wishlist_ux")
    if any(b in ["reviews_info_gaps", "fit", "size_chart", "quality"] for b in barriers):
        signals.append("4-decision_support")
    if "price_value_uncertainty" in barriers or intent == "price_monitoring":
        signals.append("5-price_budget")
    if output.external_research and "none" not in output.external_research and "unknown" not in output.external_research:
        signals.append("6-external_research")
    if segments:
        signals.append("7-segments")
        
    output.signal_families = list(set(signals))
    return output

def get_unclassified_records(session, limit=None):
    """Fetch relevant records that haven't been classified yet."""
    query = session.query(FeedbackRecord).outerjoin(Classification).filter(
        FeedbackRecord.is_relevant == True,
        Classification.id == None
    )
    if limit:
        query = query.limit(limit)
    return query.all()

def process_record_worker(record_data):
    """Worker function for threading. Takes a dict to avoid SQLAlchemy detached session issues."""
    
    if record_data.get('is_synthetic'):
        tags = record_data.get('synthetic_tags', {})
        output = ClassificationOutput(
            wishlist_relevance="wishlist_related",
            journey_stage=tags.get("journey_stage", "unknown"),
            wishlist_intent=tags.get("wishlist_intent", "unknown"),
            barrier_labels=tags.get("barrier_labels", []),
            purchase_outcome=tags.get("purchase_outcome", "unknown"),
            external_research=tags.get("external_research", [])
        )
        output = derive_segments_and_signals(output)
        return record_data['record_id'], output, None

    prompt = f"""
You are a product research analyst classifying user feedback about fashion e-commerce.

Given the following user feedback, classify it across the specified dimensions strictly following these rules:
1. wishlist_relevance: Set to "wishlist_related" ONLY if there are explicit mentions of wishlists, saved items, favorites, saving for later, or shortlisting. Otherwise, set to "shopping_generic". If incomprehensible, use "unknown".
2. wishlist_intent: MUST be "unknown" if wishlist_relevance is "shopping_generic". Only evaluate intent if it's explicitly wishlist-related.
3. journey_stage: Do NOT infer wishlist_add or wishlist_revisit unless explicitly mentioned. product/photo complaints map to "pdp", order/UX issues to "checkout", etc.
4. purchase_outcome: Rely ONLY on explicit mentions of purchasing or returning. Otherwise use "unknown" or "not_applicable". Keep "postponed" and "abandoned" strict.

Feedback: "{record_data['cleaned_text']}"
Platform: "{record_data['platform']}"
Source: "{record_data['source_type']}"
"""
    schema_str = json.dumps(ClassificationOutput.model_json_schema())
    output = None

    # Shuffle keys for this thread so traffic is distributed evenly
    keys_to_try = list(ALL_GROQ_KEYS)
    random.shuffle(keys_to_try)
    
    groq_models_to_try = [
        "openai/gpt-oss-120b", 
        "openai/gpt-oss-20b", 
        "qwen/qwen3.8-27b"
    ]

    for g_key in keys_to_try:
        if output:
            break
            
        groq_client = Groq(api_key=g_key)
        for g_model in groq_models_to_try:
            try:
                completion = groq_client.chat.completions.create(
                    model=g_model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt + f"\n\nRespond strictly with a single valid JSON object matching this exact schema:\n{schema_str}"
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                groq_response_text = completion.choices[0].message.content
                output = ClassificationOutput(**json.loads(groq_response_text))
                output = derive_segments_and_signals(output)
                return record_data['record_id'], output, None
            except Exception as ge:
                error_msg = str(ge).lower()
                if "429" in error_msg or "exhausted" in error_msg:
                    break # Break inner loop, try next API key
                continue

    # Fallback to Gemini if all Groq keys fail
    if not output and GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        google_models_to_try = [
            "gemini-3.7-flash", 
            "gemini-3.6-flash", 
            "gemini-1.5-flash", 
            "gemini-1.5-pro",
            "gemini-pro"
        ]
        
        for model in google_models_to_try:
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ClassificationOutput,
                        temperature=0.1
                    )
                )
                if hasattr(response, 'parsed') and response.parsed:
                    parsed = response.parsed
                    if isinstance(parsed, dict):
                        output = ClassificationOutput(**parsed)
                    else:
                        output = parsed
                else:
                    output = ClassificationOutput(**json.loads(response.text))
                output = derive_segments_and_signals(output)
                return record_data['record_id'], output, None
            except Exception as e:
                error_msg = str(e).lower()
                if "429" in error_msg or "404" in error_msg or "exhausted" in error_msg or "not found" in error_msg or "503" in error_msg:
                    continue
                else:
                    return record_data['record_id'], None, str(e)
                    
    return record_data['record_id'], None, "All models/keys exhausted or failed"


def classify_records(limit=None):
    if not ALL_GROQ_KEYS and not GEMINI_API_KEY:
        print("ERROR: No API keys found in .env")
        return

    print("Fetching unclassified records from database...")
    db = SessionLocal()
    records = get_unclassified_records(db, limit=limit)
    
    if not records:
        print("No unclassified records found.")
        db.close()
        return
        
    records_data = [
        {
            "record_id": r.record_id,
            "cleaned_text": r.cleaned_text,
            "platform": r.platform,
            "source_type": r.source_type,
            "is_synthetic": r.metadata_.get("is_synthetic", False) if r.metadata_ else False,
            "synthetic_tags": r.metadata_.get("synthetic_tags", {}) if r.metadata_ else {}
        } for r in records
    ]
    db.close()
    
    print(f"Found {len(records_data)} records to classify. Processing in parallel...")
    
    success_count = 0
    error_count = 0
    
    # Run in parallel. 15 max workers = 1 for each API key to maximize throughput
    max_workers = min(len(ALL_GROQ_KEYS) + 2, 20)
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_record_worker, rec): rec for rec in records_data}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            record_id, output, error = future.result()
            
            if error or not output:
                print(f"[{i}/{len(records_data)}] [ERROR] Failed to classify {record_id}: {error}")
                error_count += 1
            else:
                # Insert safely in the main thread to avoid SQLite database locks
                session = SessionLocal()
                try:
                    mapped_stage = JOURNEY_STAGE_MAP.get(output.journey_stage, "Unknown")
                    mapped_barriers = list(set([BARRIER_FAMILY_MAP.get(b, "Other") for b in output.barrier_labels]))
                    
                    classification = Classification(
                        record_id=record_id,
                        wishlist_relevance=output.wishlist_relevance,
                        journey_stage=mapped_stage,
                        wishlist_intent=output.wishlist_intent,
                        barrier_labels=mapped_barriers,
                        purchase_outcome=output.purchase_outcome,
                        external_research=output.external_research,
                        segment_tags=output.segment_tags,
                        signal_families=output.signal_families,
                        confidence=0.9, 
                        classified_at=datetime.now(timezone.utc)
                    )
                    session.add(classification)
                    session.commit()
                    success_count += 1
                    print(f"[{i}/{len(records_data)}] [OK] Classified record: {record_id}")
                except Exception as db_err:
                    session.rollback()
                    print(f"[{i}/{len(records_data)}] [DB ERROR] Failed to save {record_id}: {db_err}")
                    error_count += 1
                finally:
                    session.close()
            
            # Print progress every 50 records
            if i % 50 == 0:
                elapsed = time.time() - start_time
                print(f"--- Progress: {i}/{len(records_data)} processed in {elapsed:.1f}s. Success: {success_count}, Errors: {error_count} ---")
                
    elapsed = time.time() - start_time
    print(f"\nClassification complete in {elapsed:.1f}s.")
    print(f"Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    # Process all unclassified records
    classify_records(limit=None)
