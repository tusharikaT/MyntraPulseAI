"""
Scraper 5: Product Reviews — Trustpilot, Reviews.io, WorthEPenny, ConsumerComplaints.in.
Scrapes third-party review/complaint sites for Myntra feedback.
"""
import sys
import os
import re
import traceback
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import PRODUCT_REVIEWS_CONFIG


class ProductReviewsScraper(BaseScraper):
    """Scrape product/company reviews from third-party review sites."""

    def get_source_type(self) -> str:
        return "product_reviews"

    def _get_headers(self) -> dict:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return parsed BeautifulSoup, or None on failure."""
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            else:
                print(f"    HTTP {resp.status_code} for {url}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"    Request error for {url}: {e}")
            return None

    def _fetch_with_playwright(self, url: str) -> BeautifulSoup:
        """Fallback: fetch with Playwright."""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(30000)
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                content = page.content()
                browser.close()
                return BeautifulSoup(content, "lxml")
        except Exception as e:
            print(f"    Playwright error for {url}: {e}")
            return None

    # ── Trustpilot ──────────────────────────────────────────────

    def _scrape_trustpilot(self, base_url: str, platform_name: str) -> list:
        """Scrape Trustpilot reviews with pagination."""
        records = []
        max_pages = 10

        for page_num in range(1, max_pages + 1):
            url = f"{base_url}?page={page_num}"
            print(f"    Trustpilot page {page_num}: {url}")

            soup = self._fetch_page(url)
            if not soup:
                soup = self._fetch_with_playwright(url)
            if not soup:
                print(f"    Failed to fetch page {page_num}, stopping pagination")
                break

            # Find review cards
            review_cards = soup.find_all("article", attrs={"data-service-review-card-paper": True})
            if not review_cards:
                # Try alternative selectors
                review_cards = soup.find_all("div", class_=re.compile(r"review-card|styles_cardWrapper"))
            if not review_cards:
                # Try even broader: any section with review content
                review_cards = soup.find_all("article")

            if not review_cards:
                print(f"    No reviews found on page {page_num}, stopping pagination")
                break

            for card in review_cards:
                try:
                    # Extract review text
                    text_elem = card.find("p", attrs={"data-service-review-text-typography": True})
                    if not text_elem:
                        text_elem = card.find("p", class_=re.compile(r"review-content|styles_reviewContent"))
                    if not text_elem:
                        # Try any <p> inside the card with substantial text
                        paragraphs = card.find_all("p")
                        text_elem = max(paragraphs, key=lambda p: len(p.get_text(strip=True)), default=None) if paragraphs else None

                    raw_text = text_elem.get_text(strip=True) if text_elem else ""
                    if not raw_text or len(raw_text) < 5:
                        continue

                    # Extract title
                    title_elem = card.find("h2") or card.find("a", attrs={"data-review-title-typography": True})
                    title = title_elem.get_text(strip=True) if title_elem else ""

                    # Extract rating
                    rating = None
                    star_elem = card.find("div", attrs={"data-service-review-rating": True})
                    if star_elem:
                        rating_attr = star_elem.get("data-service-review-rating")
                        if rating_attr:
                            try:
                                rating = float(rating_attr)
                            except ValueError:
                                pass
                    if rating is None:
                        # Try img alt text like "Rated 4 out of 5 stars"
                        img = card.find("img", alt=re.compile(r"Rated \d"))
                        if img:
                            match = re.search(r"Rated (\d)", img["alt"])
                            if match:
                                rating = float(match.group(1))

                    # Extract date
                    date_published = None
                    time_elem = card.find("time")
                    if time_elem and time_elem.get("datetime"):
                        date_published = time_elem["datetime"]

                    # Extract reviewer name
                    reviewer = ""
                    name_elem = card.find("span", attrs={"data-consumer-name-typography": True})
                    if not name_elem:
                        # Try common patterns
                        name_elems = card.find_all("span")
                        for span in name_elems:
                            text = span.get_text(strip=True)
                            if text and len(text) < 50 and not text.isdigit():
                                reviewer = text
                                break

                    full_text = f"{title}\n{raw_text}".strip() if title else raw_text

                    record = RawRecord(
                        record_id=self.make_record_id(),
                        source_type="product_review",
                        platform=platform_name,
                        original_url=base_url,
                        raw_text=full_text,
                        date_published=date_published,
                        date_scraped=datetime.now(timezone.utc).isoformat(),
                        rating=rating,
                        engagement=None,
                        language="en",
                        metadata={
                            "review_site": "trustpilot",
                            "review_title": title,
                            "reviewer_name": reviewer,
                        },
                    )
                    records.append(record)

                except Exception as e:
                    print(f"    Error parsing Trustpilot review: {e}")
                    continue

            print(f"    Got {len(review_cards)} cards, {len(records)} records so far")
            self.safe_delay(PRODUCT_REVIEWS_CONFIG["delay_seconds"])

        return records

    # ── Reviews.io ──────────────────────────────────────────────

    def _scrape_reviews_io(self, base_url: str, platform_name: str) -> list:
        """Scrape reviews from Reviews.io."""
        records = []

        print(f"    Reviews.io: {base_url}")
        soup = self._fetch_page(base_url)
        if not soup:
            soup = self._fetch_with_playwright(base_url)
        if not soup:
            return records

        # Reviews.io review containers
        review_elems = soup.find_all("div", class_=re.compile(r"review[_-]?card|ReviewsWidget"))
        if not review_elems:
            # Try broader selectors
            review_elems = soup.find_all("div", class_=re.compile(r"review"))

        for elem in review_elems:
            try:
                text = elem.get_text(separator=" ", strip=True)
                if len(text) < 20:
                    continue

                # Try to extract rating
                rating = None
                star_elem = elem.find(attrs={"class": re.compile(r"star|rating")})
                if star_elem:
                    match = re.search(r"(\d(?:\.\d)?)", star_elem.get_text())
                    if match:
                        rating = float(match.group(1))

                record = RawRecord(
                    record_id=self.make_record_id(),
                    source_type="product_review",
                    platform=platform_name,
                    original_url=base_url,
                    raw_text=text[:2000],  # Cap at 2000 chars
                    date_scraped=datetime.now(timezone.utc).isoformat(),
                    rating=rating,
                    language="en",
                    metadata={"review_site": "reviews_io"},
                )
                records.append(record)

            except Exception as e:
                print(f"    Error parsing Reviews.io review: {e}")

        return records

    # ── ConsumerComplaints.in ──────────────────────────────────

    def _scrape_consumer_complaints(self, base_url: str, platform_name: str) -> list:
        """Scrape complaints from ConsumerComplaints.in."""
        records = []

        print(f"    ConsumerComplaints.in: {base_url}")
        soup = self._fetch_page(base_url)
        if not soup:
            soup = self._fetch_with_playwright(base_url)
        if not soup:
            return records

        # Complaint content
        complaint_divs = soup.find_all("div", class_=re.compile(r"complaint|review|comment"))
        if not complaint_divs:
            # Try to get the main content
            main = soup.find("article") or soup.find("main") or soup.find("div", id="content")
            if main:
                complaint_divs = [main]

        for div in complaint_divs:
            text = div.get_text(separator=" ", strip=True)
            if len(text) < 30:
                continue

            record = RawRecord(
                record_id=self.make_record_id(),
                source_type="product_review",
                platform=platform_name,
                original_url=base_url,
                raw_text=text[:3000],
                date_scraped=datetime.now(timezone.utc).isoformat(),
                language="en",
                metadata={"review_site": "consumer_complaints"},
            )
            records.append(record)

        return records

    # ── WorthEPenny ──────────────────────────────────────────────

    def _scrape_worthepenny(self, base_url: str, platform_name: str) -> list:
        """Scrape reviews from WorthEPenny."""
        records = []

        print(f"    WorthEPenny: {base_url}")
        soup = self._fetch_page(base_url)
        if not soup:
            soup = self._fetch_with_playwright(base_url)
        if not soup:
            return records

        # WorthEPenny review blocks
        review_elems = soup.find_all("div", class_=re.compile(r"review|comment|rating"))
        if not review_elems:
            # Broader: any li or div that looks like a review
            review_elems = soup.find_all(["li", "div"], class_=re.compile(r"item|entry"))

        for elem in review_elems:
            text = elem.get_text(separator=" ", strip=True)
            if len(text) < 20:
                continue

            rating = None
            rating_match = re.search(r"(\d(?:\.\d)?)\s*(?:out of|/)\s*5", text)
            if rating_match:
                rating = float(rating_match.group(1))

            record = RawRecord(
                record_id=self.make_record_id(),
                source_type="product_review",
                platform=platform_name,
                original_url=base_url,
                raw_text=text[:2000],
                date_scraped=datetime.now(timezone.utc).isoformat(),
                rating=rating,
                language="en",
                metadata={"review_site": "worthepenny"},
            )
            records.append(record)

        return records

    # ── Main scrape method ──────────────────────────────────────

    def scrape(self) -> ScrapeResult:
        """Scrape all configured review sites."""
        config = PRODUCT_REVIEWS_CONFIG
        all_records = []
        errors = 0

        site_scrapers = {
            "trustpilot": self._scrape_trustpilot,
            "reviews_io": self._scrape_reviews_io,
            "consumer_complaints": self._scrape_consumer_complaints,
            "worthepenny": self._scrape_worthepenny,
        }

        for site_key, site_config in config["platforms"].items():
            scraper_fn = site_scrapers.get(site_key)
            if not scraper_fn:
                print(f"  No scraper for site: {site_key}")
                continue

            platform_name = site_config["platform_name"]
            print(f"\n  Scraping {site_key} ({platform_name})...")

            for url in site_config["urls"]:
                try:
                    records = scraper_fn(url, platform_name)
                    all_records.extend(records)
                    print(f"  {site_key}: {len(records)} records from {url}")
                except Exception as e:
                    print(f"  ERROR scraping {site_key} {url}: {e}")
                    traceback.print_exc()
                    errors += 1

        result = ScrapeResult(
            scraper="product_reviews",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={
                "sites": list(config["platforms"].keys()),
                "delay_seconds": config["delay_seconds"],
            },
            stats={
                "total_fetched": len(all_records),
                "errors": errors,
                "by_site": {},
            },
            records=all_records,
        )

        # Count by site
        for r in all_records:
            site = r.metadata.get("review_site", "unknown")
            result.stats["by_site"][site] = result.stats["by_site"].get(site, 0) + 1

        print(f"\n[product_reviews] Done: {len(all_records)} total records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = ProductReviewsScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
