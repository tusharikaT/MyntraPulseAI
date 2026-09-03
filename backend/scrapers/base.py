"""
Base scraper interface, RawRecord dataclass, and JSON serialisation utilities.
All scrapers inherit from BaseScraper.
"""
import uuid
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict
from pathlib import Path


@dataclass
class RawRecord:
    """Standard record schema for all scraped data."""
    record_id: str                              # UUID v4
    source_type: str                            # play_store, app_store, reddit, youtube, ...
    platform: str                               # Myntra, AJIO, Nykaa, ...
    original_url: str                           # Source URL for audit
    raw_text: str                               # Original unmodified text
    date_published: Optional[str] = None        # ISO 8601 or None
    date_scraped: str = ""                      # ISO 8601
    rating: Optional[float] = None
    engagement: Optional[Dict[str, Any]] = None
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.record_id:
            self.record_id = str(uuid.uuid4())
        if not self.date_scraped:
            self.date_scraped = datetime.now(timezone.utc).isoformat()


@dataclass
class ScrapeResult:
    """Container for a scraper's output — metadata + records."""
    scraper: str
    scraped_at: str
    config_snapshot: Dict[str, Any]
    stats: Dict[str, Any]
    records: List[RawRecord]

    def to_dict(self) -> dict:
        return {
            "scraper": self.scraper,
            "scraped_at": self.scraped_at,
            "config_snapshot": self.config_snapshot,
            "stats": self.stats,
            "records": [asdict(r) for r in self.records],
        }


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def get_source_type(self) -> str:
        """Return source type identifier (e.g., 'play_store')."""
        pass

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        """Execute scraping and return a ScrapeResult."""
        pass

    def save_json(self, result: ScrapeResult) -> str:
        """Save ScrapeResult to a timestamped JSON file. Returns file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.get_source_type()}_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

        print(f"[{self.get_source_type()}] Saved {len(result.records)} records -> {filepath}")
        return str(filepath)

    def run(self) -> str:
        """Full lifecycle: scrape -> save JSON -> return file path."""
        result = self.scrape()
        return self.save_json(result)

    @staticmethod
    def matches_keywords(text: str, keywords: List[str]) -> bool:
        """Check if text matches any keyword (case-insensitive)."""
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)

    @staticmethod
    def safe_delay(seconds: float):
        """Rate-limit delay between requests."""
        time.sleep(seconds)

    @staticmethod
    def make_record_id() -> str:
        """Generate a new UUID v4 record ID."""
        return str(uuid.uuid4())
