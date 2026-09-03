import sqlite3
import os
import math
import json
from fastapi import APIRouter, Query
from typing import Optional
from api.schemas import LensResponse, LensRecordItem, Pagination

router = APIRouter()
db_path = os.path.join(os.path.dirname(__file__), "../../data/db/discovery.db")

@router.get("/lens/records", response_model=LensResponse)
def get_lens_records(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    platform: Optional[str] = None,
    source_type: Optional[str] = None,
    time_range: Optional[str] = None,
    barrier_label: Optional[str] = None,
    journey_stage: Optional[str] = None,
    theme_id: Optional[str] = None,
    wishlist_relevance: Optional[str] = None
):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = """
        FROM feedback_records r
        LEFT JOIN classifications c ON r.record_id = c.record_id
        WHERE r.is_relevant = 1
    """
    params = []

    if platform:
        base_query += " AND r.platform = ?"
        params.append(platform)
    if source_type:
        base_query += " AND r.source_type = ?"
        params.append(source_type)
    if barrier_label:
        base_query += " AND c.barrier_labels LIKE ?"
        params.append(f"%\"{barrier_label}\"%")
    if journey_stage:
        base_query += " AND c.journey_stage = ?"
        params.append(journey_stage)
    if wishlist_relevance:
        base_query += " AND c.wishlist_relevance = ?"
        params.append(wishlist_relevance)
        
    if theme_id:
        cursor.execute("SELECT theme_name FROM opportunity_themes WHERE theme_id = ?", [theme_id])
        theme_row = cursor.fetchone()
        if theme_row:
            barrier_name = theme_row["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
            base_query += " AND c.barrier_labels LIKE ?"
            params.append(f"%\"{barrier_name}\"%")

    if time_range and time_range != "all":
        if time_range == "1y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-1 year')"
        elif time_range == "3y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-3 years')"
        elif time_range == "6m":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-6 months')"
        
    # Get total count
    cursor.execute(f"SELECT COUNT(*) as total {base_query}", params)
    total_records = cursor.fetchone()["total"]

    # Get paginated data
    offset = (page - 1) * limit
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
    
    cursor.execute(data_query, params + [limit, offset])
    lens_records = cursor.fetchall()
    
    # Fetch themes map
    cursor.execute("SELECT theme_id, theme_name FROM opportunity_themes")
    theme_map = {}
    for trow in cursor.fetchall():
        barrier_key = trow["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
        theme_map[barrier_key] = {"id": trow["theme_id"], "name": trow["theme_name"]}
    
    records = []
    for row in lens_records:
        dt = row["date_published"] or row["date_scraped"]
        year = int(dt[:4]) if dt else 2024
        
        barrier_labels = []
        if row["barrier_labels"]:
            try:
                barrier_labels = json.loads(row["barrier_labels"])
            except:
                pass
                
        t_id, t_name = None, None
        if barrier_labels:
            for b in barrier_labels:
                if b in theme_map:
                    t_id = theme_map[b]["id"]
                    t_name = theme_map[b]["name"]
                    break
                
        records.append(LensRecordItem(
            record_id=row["record_id"],
            source_type=row["source_type"] or "unknown",
            platform=row["platform"] or "unknown",
            year=year,
            raw_text_snippet=row["raw_text"][:150] + "..." if row["raw_text"] and len(row["raw_text"]) > 150 else (row["raw_text"] or ""),
            barrier_labels=barrier_labels,
            journey_stage=row["journey_stage"] or "unknown",
            wishlist_relevance=row["wishlist_relevance"] or "unknown",
            wishlist_intent=row["wishlist_intent"] or "unknown",
            theme_id=t_id,
            theme_name=t_name
        ))

    conn.close()

    return LensResponse(
        data=records,
        pagination=Pagination(
            total=total_records,
            page=page,
            limit=limit,
            total_pages=math.ceil(total_records / limit) if total_records > 0 else 0
        )
    )

from api.schemas import LensInsightsResponse, LensAnalyticsResponse
from ai.llm_client import generate_insight

@router.get("/lens/analytics", response_model=LensAnalyticsResponse)
def get_lens_analytics(
    platform: Optional[str] = None,
    source_type: Optional[str] = None,
    time_range: Optional[str] = None,
    barrier_label: Optional[str] = None,
    journey_stage: Optional[str] = None,
    theme_id: Optional[str] = None,
    wishlist_relevance: Optional[str] = None
):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = """
        FROM feedback_records r
        LEFT JOIN classifications c ON r.record_id = c.record_id
        LEFT JOIN priority_scores p ON c.record_id = p.theme_id -- Note: schema may not perfectly map severity here. We will use a mock severity or fetch from opportunity_themes
        WHERE r.is_relevant = 1
    """
    params = []

    if platform:
        base_query += " AND r.platform = ?"
        params.append(platform)
    if source_type:
        base_query += " AND r.source_type = ?"
        params.append(source_type)
    if barrier_label:
        base_query += " AND c.barrier_labels LIKE ?"
        params.append(f"%\"{barrier_label}\"%")
    if journey_stage:
        base_query += " AND c.journey_stage = ?"
        params.append(journey_stage)
    if wishlist_relevance:
        base_query += " AND c.wishlist_relevance = ?"
        params.append(wishlist_relevance)
        
    if theme_id:
        cursor.execute("SELECT theme_name FROM opportunity_themes WHERE theme_id = ?", [theme_id])
        theme_row = cursor.fetchone()
        if theme_row:
            barrier_name = theme_row["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
            base_query += " AND c.barrier_labels LIKE ?"
            params.append(f"%\"{barrier_name}\"%")

    if time_range and time_range != "all":
        if time_range == "1y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-1 year')"
        elif time_range == "3y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-3 years')"
        elif time_range == "6m":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-6 months')"

    # 1. Total records
    cursor.execute(f"SELECT COUNT(*) as total {base_query}", params)
    total_records = cursor.fetchone()["total"]

    # 2. Extract barriers and outcomes for metrics
    cursor.execute(f"SELECT c.barrier_labels, c.purchase_outcome {base_query}", params)
    
    barrier_counts = {}
    outcome_counts = {}
    emotion = {"positive": 0, "neutral": 0, "negative": 0}
    
    for row in cursor.fetchall():
        # Purchase Outcomes & Emotion
        po = row["purchase_outcome"]
        if po:
            outcome_counts[po] = outcome_counts.get(po, 0) + 1
            if po in ["abandoned", "postponed"]:
                emotion["negative"] += 1
            elif po == "purchased":
                emotion["positive"] += 1
            else:
                emotion["neutral"] += 1
        else:
            emotion["neutral"] += 1
            
        # Barriers
        bl = row["barrier_labels"]
        if bl:
            try:
                barriers = json.loads(bl)
                for b in barriers:
                    barrier_counts[b] = barrier_counts.get(b, 0) + 1
            except:
                pass
                
    top_barriers = [{"barrier": k, "count": v} for k, v in sorted(barrier_counts.items(), key=lambda item: item[1], reverse=True)[:10]]
    purchase_outcomes = [{"outcome": k, "count": v} for k, v in sorted(outcome_counts.items(), key=lambda item: item[1], reverse=True)]

    # 3. Calculate Slice Friction Score (heuristic: 1-10 based on barrier density and negative outcomes)
    # If 100% have barriers and negative outcomes, score is 10.
    friction_score = 0.0
    if total_records > 0:
        negative_ratio = emotion["negative"] / total_records
        barrier_ratio = sum([b["count"] for b in top_barriers]) / total_records
        friction_score = round(min(10.0, (negative_ratio * 5) + (barrier_ratio * 5)), 1)
        
    conn.close()

    return LensAnalyticsResponse(
        total_records=total_records,
        average_severity=friction_score, # Using friction_score as proxy for severity on this slice
        top_barriers=top_barriers,
        purchase_outcomes=purchase_outcomes,
        external_research=[],
        slice_friction_score=friction_score,
        emotion_detection=emotion
    )


@router.get("/lens/insights", response_model=LensInsightsResponse)
def get_lens_insights(
    platform: Optional[str] = None,
    source_type: Optional[str] = None,
    time_range: Optional[str] = None,
    barrier_label: Optional[str] = None,
    journey_stage: Optional[str] = None,
    theme_id: Optional[str] = None,
    wishlist_relevance: Optional[str] = None
):
    # Reuse the same query logic
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = """
        FROM feedback_records r
        LEFT JOIN classifications c ON r.record_id = c.record_id
        WHERE r.is_relevant = 1
    """
    params = []

    if platform:
        base_query += " AND r.platform = ?"
        params.append(platform)
    if source_type:
        base_query += " AND r.source_type = ?"
        params.append(source_type)
    if barrier_label:
        base_query += " AND c.barrier_labels LIKE ?"
        params.append(f"%\"{barrier_label}\"%")
    if journey_stage:
        base_query += " AND c.journey_stage = ?"
        params.append(journey_stage)
    if wishlist_relevance:
        base_query += " AND c.wishlist_relevance = ?"
        params.append(wishlist_relevance)
        
    if theme_id:
        cursor.execute("SELECT theme_name FROM opportunity_themes WHERE theme_id = ?", [theme_id])
        theme_row = cursor.fetchone()
        if theme_row:
            barrier_name = theme_row["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
            base_query += " AND c.barrier_labels LIKE ?"
            params.append(f"%\"{barrier_name}\"%")

    if time_range and time_range != "all":
        if time_range == "1y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-1 year')"
        elif time_range == "3y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-3 years')"
        elif time_range == "6m":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-6 months')"

    # Fetch a sample of records for the LLM to summarize
    cursor.execute(f"SELECT r.raw_text, c.barrier_labels, c.journey_stage {base_query} ORDER BY RANDOM() LIMIT 20", params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return LensInsightsResponse(slice_summary="Not enough data to generate an insight for this slice.")
        
    context = {
        "filters_applied": {
            "platform": platform,
            "source": source_type,
            "stage": journey_stage,
            "barrier": barrier_label,
            "relevance": wishlist_relevance,
            "theme": theme_id
        },
        "sample_records": [dict(r) for r in rows]
    }
    
    prompt = "Analyze this specific slice of user feedback based on the applied filters. Provide a 2-3 sentence 'Slice Summary' explaining the core user behavior or friction point visible in this data slice."
    
    format_example = {
        "slice_summary": "Summary text here."
    }
    
    res = generate_insight(prompt, context, format_example)
    if "error" in res:
        return LensInsightsResponse(slice_summary="Failed to generate insight.")
        
    return LensInsightsResponse(**res)

