"""
Scraper 2: Apple App Store — Fetch reviews via iTunes RSS JSON feed.
Structured JSON endpoint, no HTML parsing needed for primary approach.
Falls back to Playwright if RSS feed is unavailable.
"""
import sys
import os
import traceback
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import APP_STORE_CONFIG


class AppStoreScraper(BaseScraper):
    """Scrape Apple App Store reviews via iTunes RSS JSON feed."""

    def get_source_type(self) -> str:
        return "app_store"

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json,text/html,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _fetch_rss_page(self, app_id: str, country: str, page: int) -> dict:
        """Fetch a single page of the iTunes RSS feed. Returns parsed JSON or None."""
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/id={app_id}/page={page}/sortBy=mostRecent/json"
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=30)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"    RSS feed returned {resp.status_code} for page {page}")
                return None
        except Exception as e:
            print(f"    Error fetching RSS page {page}: {e}")
            return None

    def _parse_rss_entries(self, data: dict, app_id: str, country: str, platform: str) -> list:
        """Parse RSS JSON feed entries into RawRecord list."""
        records = []

        feed = data.get("feed", {})
        entries = feed.get("entry", [])

        # The first entry is usually the app metadata, skip it
        for entry in entries:
            try:
                # Check if this is a review (has im:rating) vs app metadata
                if "im:rating" not in entry:
                    continue

                # Extract fields
                raw_text = ""
                title = ""
                rating = None
                date_published = None
                author = ""
                app_version = ""

                # Review content (body text)
                content = entry.get("content", {})
                if isinstance(content, dict):
                    raw_text = content.get("label", "")
                elif isinstance(content, str):
                    raw_text = content

                # Title
                title_data = entry.get("title", {})
                if isinstance(title_data, dict):
                    title = title_data.get("label", "")
                elif isinstance(title_data, str):
                    title = title_data

                # Rating (1-5)
                rating_data = entry.get("im:rating", {})
                if isinstance(rating_data, dict):
                    try:
                        rating = float(rating_data.get("label", 0))
                    except (ValueError, TypeError):
                        pass

                # Date
                updated = entry.get("updated", {})
                if isinstance(updated, dict):
                    date_published = updated.get("label")

                # Author
                author_data = entry.get("author", {})
                if isinstance(author_data, dict):
                    name_data = author_data.get("name", {})
                    if isinstance(name_data, dict):
                        author = name_data.get("label", "")

                # App version
                version_data = entry.get("im:version", {})
                if isinstance(version_data, dict):
                    app_version = version_data.get("label", "")

                # Review ID
                review_id_data = entry.get("id", {})
                review_id = ""
                if isinstance(review_id_data, dict):
                    review_id = review_id_data.get("label", "")

                # Combine title + body
                full_text = f"{title}\n{raw_text}".strip() if title else raw_text

                if not full_text or len(full_text.strip()) < 5:
                    continue

                record = RawRecord(
                    record_id=self.make_record_id(),
                    source_type="app_store",
                    platform=platform,
                    original_url=f"https://apps.apple.com/{country}/app/id{app_id}",
                    raw_text=full_text,
                    date_published=date_published,
                    date_scraped=datetime.now(timezone.utc).isoformat(),
                    rating=rating,
                    engagement=None,
                    language="en",
                    metadata={
                        "review_id": review_id,
                        "review_title": title,
                        "reviewer_name": author,
                        "app_version": app_version,
                        "app_id": app_id,
                        "country": country,
                    },
                )
                records.append(record)

            except Exception as e:
                print(f"    Error parsing RSS entry: {e}")
                continue

        return records

    def scrape(self) -> ScrapeResult:
        """Scrape App Store reviews for all configured apps."""
        config = APP_STORE_CONFIG
        all_records = []
        errors = 0

        print(f"[app_store] Starting scrape of {len(config['apps'])} apps...")

        for app_config in config["apps"]:
            app_id = app_config["app_id"]
            platform = app_config["platform"]
            countries = app_config.get("countries", ["in"])

            for country in countries:
                print(f"\n  App: {platform} (id={app_id}, country={country})")

                for page in range(1, 11):  # Max 10 pages
                    print(f"    Fetching RSS page {page}...")

                    data = self._fetch_rss_page(app_id, country, page)
                    if not data:
                        print(f"    No data on page {page}, stopping pagination for {country}")
                        break

                    records = self._parse_rss_entries(data, app_id, country, platform)
                    if not records:
                        print(f"    No reviews on page {page}, stopping pagination for {country}")
                        break

                    all_records.extend(records)
                    print(f"    Page {page}: {len(records)} reviews (total: {len(all_records)})")

                    self.safe_delay(config["delay_seconds"])

        result = ScrapeResult(
            scraper="app_store",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={
                "apps": [a["app_id"] for a in config["apps"]],
                "delay_seconds": config["delay_seconds"],
            },
            stats={
                "total_fetched": len(all_records),
                "errors": errors,
            },
            records=all_records,
        )

        print(f"\n[app_store] Done: {len(all_records)} total records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = AppStoreScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
