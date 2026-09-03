"""
Scraper 3: Reddit Scraper
Uses Playwright to render each thread URL, scroll to load comments, then parse with BS4.
"""
import sys
import os
import traceback
from datetime import datetime, timezone

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import REDDIT_CONFIG, KEYWORD_FILTERS


class RedditScraper(BaseScraper):
    """Scrape Reddit threads & comments using Playwright."""

    def get_source_type(self) -> str:
        return "reddit"

    def _scrape_thread(self, p, url: str, scroll_count: int, delay_seconds: float) -> list:
        records = []
        
        # Use old.reddit.com for simpler HTML structure without heavy JS framework
        old_url = url.replace("www.reddit.com", "old.reddit.com")
        print(f"  Fetching: {old_url}")

        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.set_default_timeout(30000)
            
            response = page.goto(old_url, wait_until="domcontentloaded")
            if response and response.status >= 400:
                print(f"    HTTP {response.status} for {old_url}")
                return records

            page.wait_for_timeout(3000)
            
            # Check for rate limit / over 18 warning
            html = page.content()
            if "Over18" in html or "You must be 18+ to view this community" in html:
                try:
                    button = page.locator("button:has-text('Yes')").first
                    if button.count() > 0:
                        button.click()
                        page.wait_for_timeout(2000)
                except:
                    pass
            
            if "Whoa there, pardner!" in html or response.status == 429:
                print(f"    Rate limited (429) for {old_url}")
                return records
                
            # Scroll to load comments if necessary (old reddit might not need scrolling for everything, but let's do a bit)
            for _ in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                
            html = page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Extract Subreddit
            subreddit = ""
            sub_link = soup.find("a", class_="hover may-blank")
            if sub_link and "r/" in sub_link.text:
                subreddit = sub_link.text
            else:
                # fallback from URL
                parts = old_url.split("/")
                if "r" in parts:
                    subreddit = "r/" + parts[parts.index("r") + 1]

            # Extract main post
            post_div = soup.find("div", class_="sitetable linklisting")
            if post_div:
                post_entry = post_div.find("div", class_="entry")
                if post_entry:
                    title_elem = post_entry.find("a", class_="title")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    body_elem = post_entry.find("div", class_="md")
                    body = body_elem.get_text(separator=" ", strip=True) if body_elem else ""
                    
                    author_elem = post_entry.find("a", class_="author")
                    author = author_elem.get_text(strip=True) if author_elem else ""
                    
                    score_elem = post_entry.find("div", class_="score unvoted")
                    score_text = score_elem.get("title") if score_elem else None
                    score = int(score_text) if score_text and score_text.isdigit() else None
                    
                    time_elem = post_entry.find("time")
                    timestamp = time_elem.get("datetime") if time_elem else None

                    full_text = f"{title}\n{body}".strip() if title else body
                    
                    if full_text:
                        records.append(RawRecord(
                            record_id=self.make_record_id(),
                            source_type="reddit",
                            platform="Reddit",
                            original_url=url,
                            raw_text=full_text,
                            date_published=timestamp,
                            date_scraped=datetime.now(timezone.utc).isoformat(),
                            engagement={"upvotes": score} if score is not None else None,
                            language="en",
                            metadata={
                                "subreddit": subreddit,
                                "author": author,
                                "is_post": True,
                                "depth": 0
                            },
                        ))

            # Extract comments
            comment_area = soup.find("div", class_="commentarea")
            if comment_area:
                comments = comment_area.find_all("div", class_="comment")
                for c in comments:
                    try:
                        # Determine depth based on 'unvoted' classes or nested structure.
                        # old reddit uses siteTable -> comment -> child. It's complex, we'll just store depth=1 for all for simplicity in phase 1 unless easily derived.
                        
                        entry = c.find("div", class_="entry")
                        if not entry:
                            continue
                            
                        c_body = entry.find("div", class_="md")
                        c_text = c_body.get_text(separator=" ", strip=True) if c_body else ""
                        
                        if not c_text or c_text == "[deleted]":
                            continue
                            
                        c_author_elem = entry.find("a", class_="author")
                        c_author = c_author_elem.get_text(strip=True) if c_author_elem else ""
                        
                        c_score_elem = entry.find("span", class_="score unvoted")
                        c_score_text = c_score_elem.get("title") if c_score_elem else None
                        c_score = int(c_score_text.split()[0]) if c_score_text and c_score_text.split()[0].isdigit() else None
                        
                        c_time_elem = entry.find("time")
                        c_timestamp = c_time_elem.get("datetime") if c_time_elem else None
                        
                        records.append(RawRecord(
                            record_id=self.make_record_id(),
                            source_type="reddit",
                            platform="Reddit",
                            original_url=url,
                            raw_text=c_text,
                            date_published=c_timestamp,
                            date_scraped=datetime.now(timezone.utc).isoformat(),
                            engagement={"upvotes": c_score} if c_score is not None else None,
                            language="en",
                            metadata={
                                "subreddit": subreddit,
                                "author": c_author,
                                "is_post": False,
                                "depth": 1 # simplified
                            },
                        ))
                    except Exception as e:
                        pass # Ignore individual comment errors

            print(f"    Scraped 1 post and {len(records) - 1} comments.")
            
        except Exception as e:
            print(f"    Playwright error for {old_url}: {e}")
            traceback.print_exc()
        finally:
            if browser:
                browser.close()
                
        return records

    def scrape(self) -> ScrapeResult:
        config = REDDIT_CONFIG
        all_records = []
        errors = 0

        print(f"[reddit] Starting scrape of {len(config['thread_urls'])} threads...")

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                for url in config["thread_urls"]:
                    try:
                        records = self._scrape_thread(p, url, config["scroll_count"], config["delay_seconds"])
                        all_records.extend(records)
                    except Exception as e:
                        print(f"  ERROR scraping {url}: {e}")
                        errors += 1
                        
                    self.safe_delay(config["delay_seconds"])
        except Exception as e:
             print(f"  FATAL Playwright error: {e}")
             errors += 1

        result = ScrapeResult(
            scraper="reddit",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={
                "thread_count": len(config["thread_urls"]),
                "delay_seconds": config["delay_seconds"]
            },
            stats={
                "total_fetched": len(all_records),
                "errors": errors,
            },
            records=all_records,
        )

        print(f"\n[reddit] Done: {len(all_records)} total records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = RedditScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
