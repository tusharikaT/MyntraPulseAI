"""
Scraper 4: YouTube Comments Scraper
Uses Playwright to navigate to videos, scroll to load comments, and parse with BS4.
"""
import sys
import os
import traceback
from datetime import datetime, timezone

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import YOUTUBE_CONFIG, KEYWORD_FILTERS


class YouTubeScraper(BaseScraper):
    """Scrape YouTube comments using Playwright."""

    def get_source_type(self) -> str:
        return "youtube"

    def _scrape_video(self, p, url: str, max_comments: int, delay_seconds: float) -> list:
        records = []
        print(f"  Fetching: {url}")

        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(60000)
            
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            
            # Dismiss consent dialogs if present
            try:
                button = page.locator("button:has-text('Reject all')").first
                if button.count() > 0:
                    button.click()
                    page.wait_for_timeout(1000)
            except:
                pass

            # Scroll down slightly to trigger comments load
            page.evaluate("window.scrollBy(0, 500)")
            page.wait_for_timeout(3000)

            # Keep scrolling until we have enough comments or hit the bottom
            previous_height = 0
            scroll_attempts = 0
            max_scrolls = (max_comments // 20) + 3 # roughly 20 comments per scroll
            
            for _ in range(max_scrolls):
                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                page.wait_for_timeout(delay_seconds * 1000)
                
                # Fast check to see if we have enough
                comment_count = page.locator("ytd-comment-thread-renderer").count()
                if comment_count >= max_comments:
                    break
                    
                current_height = page.evaluate("document.documentElement.scrollHeight")
                if current_height == previous_height:
                    scroll_attempts += 1
                    if scroll_attempts > 2:
                        break # reached bottom
                else:
                    scroll_attempts = 0
                    previous_height = current_height

            html = page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Extract video info
            video_title = ""
            title_elem = soup.find("h1", class_="style-scope ytd-watch-metadata")
            if title_elem:
                video_title = title_elem.get_text(strip=True)
                
            channel = ""
            channel_elem = soup.find("ytd-channel-name", class_="ytd-video-owner-renderer")
            if channel_elem:
                channel = channel_elem.get_text(strip=True)
                
            video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else ""

            # Extract comments
            comment_threads = soup.find_all("ytd-comment-thread-renderer")
            
            for thread in comment_threads[:max_comments]:
                try:
                    c_body = thread.find("yt-formatted-string", id="content-text")
                    c_text = c_body.get_text(separator=" ", strip=True) if c_body else ""
                    
                    if not c_text:
                        continue
                        
                    c_author_elem = thread.find("a", id="author-text")
                    c_author = c_author_elem.get_text(strip=True) if c_author_elem else ""
                    
                    c_time_elem = thread.find("yt-formatted-string", class_="published-time-text")
                    c_time = c_time_elem.get_text(strip=True) if c_time_elem else None
                    
                    c_likes_elem = thread.find("span", id="vote-count-middle")
                    c_likes = 0
                    if c_likes_elem:
                        likes_text = c_likes_elem.get_text(strip=True)
                        if likes_text:
                            # Handling 'K', 'M' etc is complex, we just try basic int parsing or default to 0 for phase 1.
                            if likes_text.isdigit():
                                c_likes = int(likes_text)
                            elif 'K' in likes_text:
                                c_likes = int(float(likes_text.replace('K', '')) * 1000)
                    
                    records.append(RawRecord(
                        record_id=self.make_record_id(),
                        source_type="youtube",
                        platform="YouTube",
                        original_url=url,
                        raw_text=c_text,
                        date_published=c_time,
                        date_scraped=datetime.now(timezone.utc).isoformat(),
                        engagement={"likes": c_likes} if c_likes > 0 else None,
                        language="en",
                        metadata={
                            "video_id": video_id,
                            "video_title": video_title,
                            "channel": channel,
                            "author": c_author,
                        },
                    ))
                except Exception as e:
                    pass

            print(f"    Scraped {len(records)} comments from {video_title[:30]}...")

        except Exception as e:
            print(f"    Playwright error for {url}: {e}")
            traceback.print_exc()
        finally:
            if browser:
                browser.close()
                
        return records

    def scrape(self) -> ScrapeResult:
        config = YOUTUBE_CONFIG
        all_records = []
        errors = 0

        # Note: Phase 1 relies on manually supplied video_urls.
        # Future phases could implement YouTube search via Playwright.
        
        urls_to_scrape = config.get("video_urls", [])
        if not urls_to_scrape:
             print("[youtube] WARNING: No video_urls configured. Add URLs to config/scraper_config.py to scrape YouTube.")

        print(f"[youtube] Starting scrape of {len(urls_to_scrape)} videos...")

        if urls_to_scrape:
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    for url in urls_to_scrape:
                        try:
                            records = self._scrape_video(p, url, config["max_comments_per_video"], config["scroll_pause_seconds"])
                            all_records.extend(records)
                        except Exception as e:
                            print(f"  ERROR scraping {url}: {e}")
                            errors += 1
                            
                        self.safe_delay(3) # fixed delay between videos
            except Exception as e:
                 print(f"  FATAL Playwright error: {e}")
                 errors += 1

        result = ScrapeResult(
            scraper="youtube",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={
                "video_count": len(urls_to_scrape),
                "max_comments": config["max_comments_per_video"]
            },
            stats={
                "total_fetched": len(all_records),
                "errors": errors,
            },
            records=all_records,
        )

        print(f"\n[youtube] Done: {len(all_records)} total records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = YouTubeScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
