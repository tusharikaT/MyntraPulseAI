"""
Scraper 6: Social Media Scraper
A best-effort scraper for LinkedIn public share pages using Playwright.
High risk of failure due to auth walls.
"""
import sys
import os
import traceback
from datetime import datetime, timezone

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import SOCIAL_MEDIA_CONFIG


class SocialMediaScraper(BaseScraper):
    """Scrape social media posts (primarily LinkedIn) via Playwright."""

    def get_source_type(self) -> str:
        return "social_media"

    def _scrape_post(self, p, url: str) -> list:
        records = []
        print(f"  Fetching: {url}")

        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(30000)
            
            response = page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # LinkedIn often shows a login wall. Try to close it if possible, or ignore.
            try:
                # Sometimes clicking the background or a close button helps
                close_btn = page.locator("icon[data-test-id='close-btn']").first
                if close_btn.count() > 0:
                    close_btn.click()
            except:
                pass

            html = page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Check for auth wall completely blocking content
            if "sign in" in soup.get_text().lower() and len(soup.get_text()) < 1000:
                 # We are likely blocked. Try extracting meta tags.
                 title = soup.find("meta", property="og:title")
                 desc = soup.find("meta", property="og:description")
                 
                 t_text = title["content"] if title and title.has_attr("content") else ""
                 d_text = desc["content"] if desc and desc.has_attr("content") else ""
                 
                 full_text = f"{t_text}\n{d_text}".strip()
                 if full_text:
                     records.append(RawRecord(
                        record_id=self.make_record_id(),
                        source_type="social_media",
                        platform="LinkedIn",
                        original_url=url,
                        raw_text=full_text,
                        date_published=None,
                        date_scraped=datetime.now(timezone.utc).isoformat(),
                        language="en",
                        metadata={
                            "is_meta_fallback": True
                        },
                     ))
                     print(f"    Hit Auth Wall. Extracted meta description ({len(full_text)} chars).")
                 return records

            # Main post content extraction (LinkedIn public page)
            # Find the main article or feed update
            post_container = soup.find("article") or soup.find("div", class_="feed-shared-update-v2")
            if not post_container:
                # Fallback to body if we can't find a container but there's enough text
                text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
                if len(text) > 100:
                    records.append(RawRecord(
                        record_id=self.make_record_id(),
                        source_type="social_media",
                        platform="LinkedIn",
                        original_url=url,
                        raw_text=text[:3000],
                        date_scraped=datetime.now(timezone.utc).isoformat(),
                        language="en",
                        metadata={"is_broad_fallback": True},
                    ))
                    print("    Extracted via broad fallback.")
                return records
                
            # Try to get specific parts of the article
            text_container = post_container.find("div", class_="feed-shared-text") or post_container.find("div", class_="update-components-text")
            if text_container:
                text = text_container.get_text(separator=" ", strip=True)
            else:
                text = post_container.get_text(separator=" ", strip=True)
                
            if text and len(text) > 20:
                author_container = post_container.find("span", class_="feed-shared-actor__name") or post_container.find("h3")
                author = author_container.get_text(strip=True) if author_container else ""
                
                records.append(RawRecord(
                    record_id=self.make_record_id(),
                    source_type="social_media",
                    platform="LinkedIn",
                    original_url=url,
                    raw_text=text,
                    date_scraped=datetime.now(timezone.utc).isoformat(),
                    language="en",
                    metadata={"author": author},
                ))
                print(f"    Scraped main post ({len(text)} chars).")

        except Exception as e:
            print(f"    Playwright error for {url}: {e}")
        finally:
            if browser:
                browser.close()
                
        return records

    def scrape(self) -> ScrapeResult:
        config = SOCIAL_MEDIA_CONFIG
        all_records = []
        errors = 0

        print(f"[social_media] Starting scrape of {len(config['post_urls'])} posts...")

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                for url in config["post_urls"]:
                    try:
                        records = self._scrape_post(p, url)
                        all_records.extend(records)
                    except Exception as e:
                        print(f"  ERROR scraping {url}: {e}")
                        errors += 1
                        
                    self.safe_delay(config["delay_seconds"])
        except Exception as e:
             print(f"  FATAL Playwright error: {e}")
             errors += 1

        result = ScrapeResult(
            scraper="social_media",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={
                "post_count": len(config["post_urls"]),
            },
            stats={
                "total_fetched": len(all_records),
                "errors": errors,
            },
            records=all_records,
        )

        print(f"\n[social_media] Done: {len(all_records)} total records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = SocialMediaScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
