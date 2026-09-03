"""
Scraper 7: Seed URLs — Curated blogs, articles, design case studies, academic papers.
The simplest scraper: fetch each curated URL, extract main text, save as record.
"""
import sys
import os
import traceback
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import SEED_URLS_CONFIG


class SeedURLsScraper(BaseScraper):
    """Scrape curated seed URLs (Medium articles, design case studies, etc.)."""

    def get_source_type(self) -> str:
        return "seed_urls"

    def _derive_platform(self, url: str) -> str:
        """Derive a platform name from the URL domain."""
        domain = urlparse(url).netloc.lower()
        domain_map = {
            "medium.com": "Medium",
            "nandha.design": "Nandha Design",
            "dinastipub.org": "Dinasti Journal",
            "indiatoday.in": "India Today",
            "eelet.org.uk": "EELET",
            "scribd.com": "Scribd",
        }
        for key, name in domain_map.items():
            if key in domain:
                return name
        return domain

    def _extract_main_text(self, soup: BeautifulSoup, url: str) -> str:
        """Extract the main article text from a parsed page."""
        # Try <article> tag first (works for Medium, many blogs)
        article = soup.find("article")
        if article:
            text = article.get_text(separator="\n", strip=True)
            if len(text) > 100:
                return text

        # Try <main> tag
        main = soup.find("main")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if len(text) > 100:
                return text

        # Try common content divs
        for selector in [
            {"class_": "post-content"},
            {"class_": "article-body"},
            {"class_": "entry-content"},
            {"class_": "content"},
            {"id": "content"},
            {"role": "main"},
        ]:
            div = soup.find("div", **selector)
            if div:
                text = div.get_text(separator="\n", strip=True)
                if len(text) > 100:
                    return text

        # Fallback: find the largest text block in the page
        # Get all divs, sort by text length, pick the longest
        divs = soup.find_all("div")
        if divs:
            longest = max(divs, key=lambda d: len(d.get_text(strip=True)))
            text = longest.get_text(separator="\n", strip=True)
            if len(text) > 50:
                return text

        # Last resort: full body text
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)[:5000]

        return ""

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try <h1> first
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        # Try <title>
        title = soup.find("title")
        if title:
            return title.get_text(strip=True)

        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        return ""

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"]

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"]

        return ""

    def _fetch_with_requests(self, url: str) -> tuple:
        """Fetch URL with requests. Returns (html_content, status_code) or (None, error_code)."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            return resp.text, resp.status_code
        except requests.exceptions.RequestException as e:
            print(f"  [requests] Error fetching {url}: {e}")
            return None, 0

    def _fetch_with_playwright(self, url: str) -> tuple:
        """Fallback: fetch URL with Playwright headless browser."""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(30000)
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)  # Wait for JS rendering
                content = page.content()
                browser.close()
                return content, 200
        except Exception as e:
            print(f"  [playwright] Error fetching {url}: {e}")
            return None, 0

    def scrape(self) -> ScrapeResult:
        """Scrape all seed URLs and return structured results."""
        config = SEED_URLS_CONFIG
        records = []
        errors = 0
        total_attempted = 0

        print(f"[seed_urls] Starting scrape of {len(config['urls'])} seed URLs...")

        for entry in config["urls"]:
            url = entry["url"]
            url_type = entry["type"]
            total_attempted += 1

            print(f"  [{total_attempted}/{len(config['urls'])}] Fetching: {url}")

            # Try requests first
            html, status = self._fetch_with_requests(url)

            if html is None or status >= 400:
                print(f"  [requests] Failed (status={status}), trying Playwright...")
                html, status = self._fetch_with_playwright(url)

            if html is None or status >= 400:
                print(f"  SKIPPED: Could not fetch {url}")
                errors += 1
                self.safe_delay(config["delay_seconds"])
                continue

            # Parse HTML
            soup = BeautifulSoup(html, "lxml")

            # Extract content
            title = self._extract_title(soup)
            description = self._extract_meta_description(soup)
            main_text = self._extract_main_text(soup, url)

            if not main_text or len(main_text.strip()) < 20:
                print(f"  WARNING: Very little text extracted from {url} ({len(main_text)} chars)")
                # Still save whatever we got — don't skip

            # Create record
            record = RawRecord(
                record_id=self.make_record_id(),
                source_type="web_article",
                platform=self._derive_platform(url),
                original_url=url,
                raw_text=main_text,
                date_published=None,  # Hard to extract reliably across sites
                date_scraped=datetime.now(timezone.utc).isoformat(),
                rating=None,
                engagement=None,
                language="en",
                metadata={
                    "url_type": url_type,
                    "page_title": title,
                    "meta_description": description,
                    "text_length": len(main_text),
                },
            )
            records.append(record)
            print(f"  OK: {title[:60]}... ({len(main_text)} chars)")

            self.safe_delay(config["delay_seconds"])

        # Build result
        result = ScrapeResult(
            scraper="seed_urls",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={"url_count": len(config["urls"]), "delay_seconds": config["delay_seconds"]},
            stats={
                "total_attempted": total_attempted,
                "total_fetched": len(records),
                "errors": errors,
                "duration_seconds": 0,  # Will be calculated by run_all.py
            },
            records=records,
        )

        print(f"[seed_urls] Done: {len(records)} records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = SeedURLsScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
