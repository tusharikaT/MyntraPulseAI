import sqlite3
import os
import json
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any
from api.schemas import OverviewResponse

router = APIRouter()
db_path = os.path.join(os.path.dirname(__file__), "../../data/db/discovery.db")

@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    platform: Optional[str] = None,
    time_range: Optional[str] = None # e.g., "1y", "3y", "all"
):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    base_query = "FROM feedback_records r LEFT JOIN classifications c ON r.record_id = c.record_id WHERE r.is_relevant = 1"
    params = []
    
    if platform:
        base_query += " AND r.platform = ?"
        params.append(platform)
        
    if time_range and time_range != "all":
        if time_range == "1y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-1 year')"
        elif time_range == "3y":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-3 years')"
        elif time_range == "6m":
            base_query += " AND COALESCE(r.date_published, r.date_scraped) >= date('now', '-6 months')"

    # 1. Total records
    cursor.execute(f"SELECT COUNT(*) as cnt {base_query}", params)
    reviews_analyzed = cursor.fetchone()["cnt"]

    # 2. Average Severity
    cursor.execute("SELECT AVG(severity) as avg_sev FROM priority_scores")
    avg_sev_row = cursor.fetchone()
    average_severity = round(avg_sev_row["avg_sev"], 2) if avg_sev_row and avg_sev_row["avg_sev"] else 0.0

    # 3. Theme count
    cursor.execute("SELECT COUNT(*) as cnt FROM opportunity_themes")
    theme_count = cursor.fetchone()["cnt"]

    # 4. Sources
    cursor.execute(f"""
        SELECT r.source_type, COUNT(*) as cnt, MIN(r.date_published) as min_date, MAX(r.date_published) as max_date 
        {base_query} GROUP BY r.source_type
    """, params)
    sources = []
    for row in cursor.fetchall():
        min_yr = row["min_date"][:4] if row["min_date"] else "2020"
        max_yr = row["max_date"][:4] if row["max_date"] else "2024"
        sources.append({
            "source_type": row["source_type"] or "unknown",
            "total_records": row["cnt"],
            "year_coverage": f"{min_yr}-{max_yr}"
        })

    # 5. Reviews by Year
    cursor.execute(f"""
        SELECT strftime('%Y', COALESCE(r.date_published, r.date_scraped)) as year, COUNT(*) as cnt 
        {base_query} GROUP BY year ORDER BY year
    """, params)
    reviews_by_year = [{"year": row["year"], "count": row["cnt"]} for row in cursor.fetchall() if row["year"]]

    # 6. Barrier Breakdown
    cursor.execute(f"""
        SELECT c.barrier_labels
        {base_query}
    """, params)
    
    barrier_counts = {}
    for row in cursor.fetchall():
        if row["barrier_labels"]:
            try:
                barriers = json.loads(row["barrier_labels"])
                for b in barriers:
                    barrier_counts[b] = barrier_counts.get(b, 0) + 1
            except:
                pass
                
    barrier_breakdown = [{"barrier": k, "count": v} for k, v in sorted(barrier_counts.items(), key=lambda item: item[1], reverse=True)[:10]]

    # 7. Source Mix
    source_mix = []
    if reviews_analyzed > 0:
        source_mix = [{"source_type": s["source_type"], "percentage": round((s["total_records"] / reviews_analyzed) * 100, 1)} for s in sources]

    # 8. New Aggregations
    cursor.execute(f"""
        SELECT c.journey_stage, c.wishlist_intent, c.purchase_outcome, c.segment_tags, c.barrier_labels
        {base_query}
    """, params)
    
    journey_counts = {}
    intent_counts = {}
    outcome_counts = {}
    segment_counts = {}
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}

    for row in cursor.fetchall():
        if row["journey_stage"]:
            try:
                stages = json.loads(row["journey_stage"]) if isinstance(row["journey_stage"], str) and row["journey_stage"].startswith("[") else [row["journey_stage"]]
                for s in stages:
                    journey_counts[s] = journey_counts.get(s, 0) + 1
            except:
                journey_counts[row["journey_stage"]] = journey_counts.get(row["journey_stage"], 0) + 1
                
        if row["wishlist_intent"]:
            try:
                intents = json.loads(row["wishlist_intent"]) if isinstance(row["wishlist_intent"], str) and row["wishlist_intent"].startswith("[") else [row["wishlist_intent"]]
                for i in intents:
                    intent_counts[i] = intent_counts.get(i, 0) + 1
            except:
                intent_counts[row["wishlist_intent"]] = intent_counts.get(row["wishlist_intent"], 0) + 1
                
        if row["purchase_outcome"]:
            outcome_counts[row["purchase_outcome"]] = outcome_counts.get(row["purchase_outcome"], 0) + 1
            
        if row["segment_tags"]:
            try:
                segs = json.loads(row["segment_tags"])
                for s in segs:
                    segment_counts[s] = segment_counts.get(s, 0) + 1
            except:
                pass
                
        # Sentiment heuristic
        is_negative = False
        is_positive = False
        if row["purchase_outcome"] in ["abandoned", "postponed"]:
            is_negative = True
        elif row["purchase_outcome"] == "purchased":
            is_positive = True
            
        if row["barrier_labels"]:
            # If any barriers exist, we lean negative or neutral
            if is_positive:
                is_positive = False # mixed feelings -> neutral
            else:
                is_negative = True
                
        if is_negative:
            sentiment_counts["negative"] += 1
        elif is_positive:
            sentiment_counts["positive"] += 1
        else:
            sentiment_counts["neutral"] += 1
                
    journey_stages = [{"stage": k, "count": v} for k, v in sorted(journey_counts.items(), key=lambda item: item[1], reverse=True)]
    wishlist_intents = [{"intent": k, "count": v} for k, v in sorted(intent_counts.items(), key=lambda item: item[1], reverse=True)]
    purchase_outcomes = [{"outcome": k, "count": v} for k, v in sorted(outcome_counts.items(), key=lambda item: item[1], reverse=True)]
    segment_mentions = [{"segment": k, "count": v} for k, v in sorted(segment_counts.items(), key=lambda item: item[1], reverse=True)]
    sentiment_breakdown = [{"sentiment": k, "count": v} for k, v in sentiment_counts.items()]

    # 9. Recent Verbatims
    cursor.execute(f"SELECT r.platform, r.source_type, r.raw_text, COALESCE(r.date_published, r.date_scraped) as dt {base_query} ORDER BY dt DESC LIMIT 3", params)
    recent_verbatims = [{"platform": row["platform"], "source": row["source_type"], "text": row["raw_text"]} for row in cursor.fetchall()]

    conn.close()

    return OverviewResponse(
        last_sync=None,
        reviews_analyzed=reviews_analyzed,
        average_severity=average_severity,
        theme_count=theme_count,
        sources=sources,
        reviews_by_year=reviews_by_year,
        barrier_breakdown=barrier_breakdown,
        source_mix=source_mix,
        journey_stages=journey_stages,
        wishlist_intents=wishlist_intents,
        purchase_outcomes=purchase_outcomes,
        segment_mentions=segment_mentions,
        sentiment_breakdown=sentiment_breakdown,
        recent_verbatims=recent_verbatims
    )

from api.schemas import OverviewInsightsResponse
from ai.llm_client import generate_insight

@router.get("/overview/insights", response_model=OverviewInsightsResponse)
def get_overview_insights(
    platform: Optional[str] = None,
    time_range: Optional[str] = None
):
    overview_data = get_overview(platform, time_range)
    
    # Fetch top themes for additional context
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT theme_name, pm_priority_score, prevalence, severity FROM opportunity_themes JOIN priority_scores USING(theme_id) ORDER BY pm_priority_score DESC LIMIT 5")
    themes = [dict(row) for row in cursor.fetchall()]
    conn.close()

    context = {
        "metrics": {
            "reviews_analyzed": overview_data.reviews_analyzed,
            "average_severity": overview_data.average_severity,
            "top_barriers": [b["barrier"] for b in overview_data.barrier_breakdown[:5]]
        },
        "top_themes": themes
    }

    prompt = "Based on the overview metrics and top themes, generate an executive summary. Identify the absolute biggest 'hero problem', 2-3 key pain points driving it, and 1-2 areas where we need more user validation before acting."
    
    format_example = {
        "hero_problem": {
            "title": "Short title",
            "description": "1-2 sentence description",
            "impact_score": "high/medium/low"
        },
        "painpoints": [
            {"title": "Pain point name", "context": "Why it happens"}
        ],
        "needs_validation": [
            {"area": "What to investigate", "reason": "Why it's unclear"}
        ]
    }
    
    insight_res = generate_insight(prompt, context, format_example)
    if "error" in insight_res:
        return OverviewInsightsResponse(
            hero_problem={"title": "Error generating insight", "description": insight_res["error"], "impact_score": "low"},
            painpoints=[],
            needs_validation=[]
        )
        
    return OverviewInsightsResponse(**insight_res)

