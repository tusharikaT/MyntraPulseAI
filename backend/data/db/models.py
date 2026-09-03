"""
SQLAlchemy models for the Discovery Engine Storage Layer.
"""
from datetime import datetime, timezone
import uuid
import os
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, 
    Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class SyncRun(Base):
    __tablename__ = 'sync_runs'
    
    sync_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20)) # running, success, failed
    config_snapshot = Column(JSON, nullable=True)
    summary = Column(JSON, nullable=True)
    
    # Relationships
    logs = relationship("StageLog", back_populates="sync_run")
    records = relationship("FeedbackRecord", back_populates="sync_run")


class StageLog(Base):
    __tablename__ = 'stage_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_id = Column(String(36), ForeignKey('sync_runs.sync_id'))
    stage = Column(String(50)) # raw, english, relevant, cleaned, final
    source_type = Column(String(50))
    platform = Column(String(50))
    count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    errors = Column(JSON, nullable=True)
    
    sync_run = relationship("SyncRun", back_populates="logs")


class FeedbackRecord(Base):
    """
    Central storage for scraped records. 
    record_id is the PK to support Upsert/Append for the "Sync Reviews" feature.
    """
    __tablename__ = 'feedback_records'
    
    record_id = Column(String(36), primary_key=True)
    sync_id = Column(String(36), ForeignKey('sync_runs.sync_id'), nullable=True)
    source_type = Column(String(50))
    platform = Column(String(50))
    original_url = Column(Text, nullable=True)
    date_published = Column(DateTime, nullable=True)
    date_scraped = Column(DateTime, nullable=False)
    raw_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    language = Column(String(10), default="en")
    rating = Column(Float, nullable=True)
    engagement = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True) # avoiding reserved word clash
    is_relevant = Column(Boolean, default=False)
    
    # Relationships
    sync_run = relationship("SyncRun", back_populates="records")
    classification = relationship("Classification", back_populates="record", uselist=False)


class Classification(Base):
    __tablename__ = 'classifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_id = Column(String(36), ForeignKey('feedback_records.record_id'), unique=True)
    
    wishlist_relevance = Column(String(50))
    journey_stage = Column(String(50))
    wishlist_intent = Column(String(50))
    barrier_labels = Column(JSON) # array of strings
    purchase_outcome = Column(String(50))
    external_research = Column(JSON) # array of strings
    segment_tags = Column(JSON) # array of strings
    signal_families = Column(JSON) # array of strings
    
    confidence = Column(Float, nullable=True)
    classified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    record = relationship("FeedbackRecord", back_populates="classification")


class OpportunityTheme(Base):
    __tablename__ = 'opportunity_themes'
    
    theme_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    theme_name = Column(String(200))
    description = Column(Text)
    signal_family = Column(String(50))
    record_count = Column(Integer, default=0)
    representative_quotes = Column(JSON)
    affected_segments = Column(JSON)
    journey_stages = Column(JSON)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    score = relationship("PriorityScore", back_populates="theme", uselist=False)


class PriorityScore(Base):
    __tablename__ = 'priority_scores'
    
    theme_id = Column(String(36), ForeignKey('opportunity_themes.theme_id'), primary_key=True)
    prevalence = Column(Float)
    severity = Column(Float)
    metric_proximity = Column(Float)
    cross_source_consistency = Column(Float)
    addressability = Column(Float)
    pm_priority_score = Column(Float)
    score_breakdown = Column(JSON)
    scored_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    theme = relationship("OpportunityTheme", back_populates="score")

# Database connection setup
db_dir = os.path.dirname(__file__)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)
    
DB_PATH = os.path.join(db_dir, 'discovery.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DB_PATH}")

if __name__ == "__main__":
    init_db()
