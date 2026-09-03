import sqlite3
import os
import json
from fastapi import APIRouter
from api.schemas import ThemesResponse, ThemeItem

router = APIRouter()
db_path = os.path.join(os.path.dirname(__file__), "../../data/db/discovery.db")

@router.get("/themes", response_model=ThemesResponse)
def get_themes():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            t.theme_id, 
            t.theme_name, 
            t.record_count,
            t.affected_segments,
            t.journey_stages,
            s.pm_priority_score,
            s.prevalence,
            s.severity,
            s.metric_proximity,
            s.cross_source_consistency,
            s.addressability,
            s.score_breakdown
        FROM opportunity_themes t
        JOIN priority_scores s ON t.theme_id = s.theme_id
        ORDER BY s.pm_priority_score DESC
    """
    cursor.execute(query)
    
    themes = []
    for row in cursor.fetchall():
        try:
            dominant_stages = json.loads(row["journey_stages"]) if row["journey_stages"] else []
        except:
            dominant_stages = []
            
        # The schema requires dominant_barriers and source_types_present. 
        # Since OpportunityTheme maps 1:1 to a barrier currently (cluster.py), 
        # we extract the barrier from the theme_name "Friction: {barrier}"
        barrier = row["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
        
        themes.append(ThemeItem(
            theme_id=row["theme_id"],
            theme_name=row["theme_name"],
            pm_priority_score=round(row["pm_priority_score"], 4),
            prevalence=round(row["prevalence"], 4),
            severity=round(row["severity"], 4),
            metric_proximity=round(row["metric_proximity"], 4),
            cross_source_consistency=round(row["cross_source_consistency"], 4),
            addressability=round(row["addressability"], 4),
            record_count=row["record_count"],
            dominant_barriers=[barrier],
            dominant_stages=dominant_stages[:3],
            source_types_present=[], # We omitted saving this directly in cluster.py, but radar doesn't strictly break if empty
            score_breakdown=json.loads(row["score_breakdown"]) if row["score_breakdown"] else {}
        ))

    conn.close()
    return ThemesResponse(themes=themes)

from api.schemas import ThemeInsightsResponse, ThemeExamplesResponse
from ai.llm_client import generate_insight

@router.get("/themes/insights", response_model=ThemeInsightsResponse)
def get_themes_insights():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT theme_id, theme_name, record_count FROM opportunity_themes JOIN priority_scores USING(theme_id) ORDER BY pm_priority_score DESC LIMIT 5")
    rows = [dict(r) for r in cursor.fetchall()]
    
    # We also need a sample of records for each theme to give context for root causes
    context_themes = []
    for row in rows:
        barrier_name = row["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
        cursor.execute("SELECT raw_text FROM feedback_records r JOIN classifications c ON r.record_id = c.record_id WHERE r.is_relevant=1 AND c.barrier_labels LIKE ? LIMIT 5", [f'%"{barrier_name}"%'])
        samples = [r["raw_text"] for r in cursor.fetchall()]
        row["sample_feedback"] = samples
        context_themes.append(row)
        
    conn.close()
    
    if not context_themes:
        return ThemeInsightsResponse(themes=[])
        
    prompt = "For the provided top opportunity themes and their sample feedback, generate a root cause hypothesis, a product opportunity (what we can build/fix), and a 1-sentence summary for each."
    
    format_example = {
        "themes": [
            {
                "theme_id": "theme-123",
                "root_cause": "Why this is happening",
                "opportunity": "How PMs can solve this",
                "summary": "1 sentence executive summary"
            }
        ]
    }
    
    res = generate_insight(prompt, {"top_themes": context_themes}, format_example)
    if "error" in res:
        return ThemeInsightsResponse(themes=[])
        
    return ThemeInsightsResponse(**res)

@router.get("/themes/{theme_id}/examples", response_model=ThemeExamplesResponse)
def get_theme_examples(theme_id: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT theme_name FROM opportunity_themes WHERE theme_id = ?", [theme_id])
    theme_row = cursor.fetchone()
    if not theme_row:
        conn.close()
        return ThemeExamplesResponse(examples=[])
        
    barrier_name = theme_row["theme_name"].replace("Friction: ", "").lower().replace(" ", "_")
    
    cursor.execute(
        "SELECT r.record_id, r.platform, r.source_type, r.raw_text, c.journey_stage FROM feedback_records r JOIN classifications c ON r.record_id = c.record_id WHERE r.is_relevant=1 AND c.barrier_labels LIKE ? ORDER BY RANDOM() LIMIT 5", 
        [f'%"{barrier_name}"%']
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return ThemeExamplesResponse(examples=rows)

