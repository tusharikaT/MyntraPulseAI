"""
Theme Clustering and PM Priority Scoring Engine.
Aggregates classified records into themes and scores them.
"""
import os
import sys
import uuid
import json
from datetime import datetime, timezone
from collections import defaultdict
from sqlalchemy import func

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.db.models import SessionLocal, FeedbackRecord, Classification, OpportunityTheme, PriorityScore

def generate_themes_and_scores():
    db = SessionLocal()
    
    # We will cluster simply by aggregating records by their barrier labels.
    # Since barrier_labels is a JSON array, we need to fetch all classifications and explode them in python.
    classifications = db.query(Classification).all()
    
    if not classifications:
        print("No classifications found. Run classifier first.")
        db.close()
        return

    # 1. Group records by barrier
    barrier_groups = defaultdict(list)
    total_records = len(classifications)
    
    for c in classifications:
        barriers = c.barrier_labels
        if not barriers:
            barriers = ["other"]
            
        for b in barriers:
            barrier_groups[b].append(c)

    print(f"Found {len(barrier_groups)} unique themes (barriers).")
    
    # 2. Compute Priority Score for each theme
    # Clear existing themes to recalculate
    db.query(PriorityScore).delete()
    db.query(OpportunityTheme).delete()
    db.commit()
    
    for barrier, records in barrier_groups.items():
        record_count = len(records)
        
        # Calculate dimensions
        prevalence = record_count / total_records
        
        # Severity: placeholder calculation based on volume (in real world, requires sentiment analysis)
        severity = min(1.0, record_count / 100) 
        
        # Metric Proximity: Calculate % of records in high-value journey stages
        high_value_stages = ["Purchase", "Product evaluation", "Shortlist / intent"]
        high_value_count = sum(1 for r in records if r.journey_stage in high_value_stages)
        metric_proximity = high_value_count / record_count if record_count > 0 else 0
        
        # Cross Source Consistency: How many distinct source types does this barrier appear in?
        source_types = set()
        for r in records:
            if r.record and r.record.source_type:
                source_types.add(r.record.source_type)
        
        cross_source_consistency = len(source_types) / 7.0 # Max 7 sources
        
        # Addressability: Fixed heuristic per barrier for now
        addressability_map = {
            "Fit & sizing": 0.8, 
            "Quality & material": 0.7,
            "Price & value": 0.9, 
            "Comparison difficulty": 0.8,
            "Information gaps": 0.9,
            "Wishlist UX": 0.8,
            "Availability": 0.4,
            "Logistics": 0.6
        }
        addressability = addressability_map.get(barrier, 0.5)
        
        # Compute final PM Score
        pm_score = (
            (0.30 * prevalence) +
            (0.25 * severity) +
            (0.25 * metric_proximity) +
            (0.10 * cross_source_consistency) +
            (0.10 * addressability)
        )
        
        # Create Theme
        theme_id = str(uuid.uuid4())
        
        # Aggregate segments & stages for metadata
        affected_segments = list(set([seg for r in records for seg in r.segment_tags]))
        journey_stages = list(set([r.journey_stage for r in records]))
        
        theme = OpportunityTheme(
            theme_id=theme_id,
            theme_name=f"Friction: {barrier}",
            description=f"Users experiencing issues with {barrier} across {len(source_types)} platforms.",
            signal_family="2-purchase_barriers",
            record_count=record_count,
            representative_quotes=[], # Would need text join here
            affected_segments=affected_segments,
            journey_stages=journey_stages
        )
        
        score = PriorityScore(
            theme_id=theme_id,
            prevalence=prevalence,
            severity=severity,
            metric_proximity=metric_proximity,
            cross_source_consistency=cross_source_consistency,
            addressability=addressability,
            pm_priority_score=pm_score,
            score_breakdown={
                "prevalence": prevalence,
                "severity": severity,
                "metric_proximity": metric_proximity,
                "cross_source_consistency": cross_source_consistency,
                "addressability": addressability
            }
        )
        
        db.add(theme)
        db.add(score)
        
    db.commit()
    print("Theme clustering and priority scoring complete!")
    db.close()

if __name__ == "__main__":
    generate_themes_and_scores()
