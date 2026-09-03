from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class StageLogResponse(BaseModel):
    stage: str
    count: int

class SyncStatus(BaseModel):
    sync_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    stage_logs: List[StageLogResponse]

class OverviewResponse(BaseModel):
    last_sync: Optional[SyncStatus] = None
    reviews_analyzed: int
    average_severity: float
    theme_count: int
    sources: List[Dict[str, Any]]
    reviews_by_year: List[Dict[str, Any]]
    barrier_breakdown: List[Dict[str, Any]]
    source_mix: List[Dict[str, Any]]
    journey_stages: List[Dict[str, Any]] = []
    wishlist_intents: List[Dict[str, Any]] = []
    purchase_outcomes: List[Dict[str, Any]] = []
    segment_mentions: List[Dict[str, Any]] = []
    sentiment_breakdown: List[Dict[str, Any]] = []
    recent_verbatims: List[Dict[str, Any]] = []
    
class LensAnalyticsResponse(BaseModel):
    total_records: int
    average_severity: float
    top_barriers: List[Dict[str, Any]]
    purchase_outcomes: List[Dict[str, Any]]
    external_research: List[Dict[str, Any]]
    slice_friction_score: float = 0.0
    emotion_detection: Dict[str, Any] = {"positive": 0, "neutral": 0, "negative": 0}

class LensRecordItem(BaseModel):
    record_id: str
    source_type: str
    platform: str
    year: int
    raw_text_snippet: str
    barrier_labels: List[str]
    journey_stage: str
    wishlist_relevance: str
    wishlist_intent: str
    theme_id: Optional[str] = None
    theme_name: Optional[str] = None

class Pagination(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int

class LensResponse(BaseModel):
    data: List[LensRecordItem]
    pagination: Pagination

class ThemeItem(BaseModel):
    theme_id: str
    theme_name: str
    pm_priority_score: float
    prevalence: float
    severity: float
    metric_proximity: float
    cross_source_consistency: float
    addressability: float
    record_count: int
    dominant_barriers: List[str]
    dominant_stages: List[str]
    source_types_present: List[str]
    score_breakdown: Dict[str, float]

class ThemesResponse(BaseModel):
    themes: List[ThemeItem]

class SourceCitation(BaseModel):
    record_id: str
    quote: str
    original_url: str
    platform: str
    source_type: str
    rating: Optional[float] = None

class CopilotResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    dataset_summary: Dict[str, Any]
    suggested_followups: List[str]

class CopilotRequest(BaseModel):
    question: str
    platform: Optional[str] = None
    time_range: Optional[str] = None
    barrier_label: Optional[str] = None
    theme_id: Optional[str] = None

class OverviewInsightsResponse(BaseModel):
    hero_problem: Dict[str, Any]
    painpoints: List[Dict[str, Any]]
    needs_validation: List[Dict[str, Any]]

class LensInsightsResponse(BaseModel):
    slice_summary: str

class ThemeInsightItem(BaseModel):
    theme_id: str
    root_cause: str
    opportunity: str
    summary: str

class ThemeInsightsResponse(BaseModel):
    themes: List[ThemeInsightItem]

class ThemeExamplesResponse(BaseModel):
    examples: List[Dict[str, Any]]
