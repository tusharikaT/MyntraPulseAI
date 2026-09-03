"""
CLI to run scrapers individually or all at once.

Usage:
    python -m scrapers.run_all                    # Run all scrapers
    python -m scrapers.run_all google_play        # Run specific scraper
    python -m scrapers.run_all google_play reddit  # Run multiple scrapers
"""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import all scrapers
from scrapers.google_play import GooglePlayScraper
from scrapers.app_store import AppStoreScraper
from scrapers.reddit import RedditScraper
from scrapers.youtube import YouTubeScraper
from scrapers.product_reviews import ProductReviewsScraper
from scrapers.social_media import SocialMediaScraper
from scrapers.seed_urls import SeedURLsScraper

SCRAPERS = {
    "google_play": GooglePlayScraper,
    "app_store": AppStoreScraper,
    "reddit": RedditScraper,
    "youtube": YouTubeScraper,
    "product_reviews": ProductReviewsScraper,
    "social_media": SocialMediaScraper,
    "seed_urls": SeedURLsScraper,
}

def run_scraper(name: str) -> dict:
    """Run a single scraper and return summary stats."""
    print(f"\n{'='*60}")
    print(f"  Running: {name}")
    print(f"{'='*60}")

    scraper_class = SCRAPERS[name]
    scraper = scraper_class()

    start = time.time()
    try:
        filepath = scraper.run()
        duration = time.time() - start
        return {"name": name, "status": "success", "file": filepath, "duration": duration}
    except Exception as e:
        duration = time.time() - start
        print(f"[{name}] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"name": name, "status": "error", "error": str(e), "duration": duration}

def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(SCRAPERS.keys())

    # Validate target names
    for t in targets:
        if t not in SCRAPERS:
            print(f"Unknown scraper: {t}. Available: {', '.join(SCRAPERS.keys())}")
            sys.exit(1)

    print(f"Myntra Discovery Engine — Scraper Run")
    print(f"Targets: {', '.join(targets)}")
    print(f"Started: {datetime.now().isoformat()}")

    results = []
    for name in targets:
        result = run_scraper(name)
        results.append(result)

    # Print summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    for r in results:
        status = "[OK]" if r["status"] == "success" else "[FAIL]"
        print(f"  {status} {r['name']:20s} — {r['duration']:>5.1f}s — {r.get('file', r.get('error', ''))}")

if __name__ == "__main__":
    main()
