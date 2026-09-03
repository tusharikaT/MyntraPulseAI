"""
Scraper 1: Google Play Store — Fetch app reviews.
Uses Playwright to navigate, click "See all reviews", scroll, and extract via BeautifulSoup.
"""
import sys
import os
import re
import traceback
from datetime import datetime, timezone

from bs4 import BeautifulSoup

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scrapers.base import BaseScraper, RawRecord, ScrapeResult
from config.scraper_config import GOOGLE_PLAY_CONFIG, KEYWORD_FILTERS


class GooglePlayScraper(BaseScraper):
    """Scrape Google Play Store reviews using Playwright for pagination."""

    def get_source_type(self) -> str:
        return "play_store"

    def _parse_date(self, date_str: str) -> str:
        """Attempt to standardize date strings if possible, else return as-is."""
        if not date_str:
            return None
        return date_str.strip()

    def _scrape_app(self, p, app_id: str, platform: str, max_reviews: int, delay_seconds: float) -> list:
        """Scrape reviews for a single app."""
        records = []
        url = f"https://play.google.com/store/apps/details?id={app_id}&hl=en&gl=in"
        print(f"  Fetching: {url}")

        browser = None
        try:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(30000)
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Look for "See all reviews" or similar button.
            # In Google Play, it's often a button with an arrow in the ratings section.
            # We can try to find buttons containing text like "See all reviews"
            try:
                # Find the button that opens the modal.
                # A robust way is looking for a span with text "See all reviews" and clicking its parent button.
                button = page.locator("button:has-text('See all reviews')").first
                if button.count() > 0:
                    button.click()
                    page.wait_for_timeout(2000)
                else:
                    # Alternative text
                    button = page.locator("span:text-is('See all reviews')").first
                    if button.count() > 0:
                        button.click()
                        page.wait_for_timeout(2000)
                    else:
                        print(f"    Could not find 'See all reviews' button for {app_id}. Scraping visible page only.")
            except Exception as e:
                print(f"    Error clicking 'See all reviews': {e}")

            # Now we are either in the modal or on the main page.
            # We need to scroll down to load more reviews.
            # If in modal, we must scroll the modal's internal scroll container.
            # Finding the scroll container:
            scroll_attempts = 0
            max_scrolls = (max_reviews // 40) + 2  # Approximate

            previous_review_count = 0
            
            # The reviews modal usually has role="dialog".
            dialog = page.locator("div[role='dialog']").first
            
            for i in range(max_scrolls):
                if dialog.count() > 0:
                    # Scroll the dialog's child that is scrollable
                    page.evaluate("""(dialog) => {
                        const scrollable = Array.from(dialog.querySelectorAll('div')).find(div => div.scrollHeight > div.clientHeight);
                        if(scrollable) scrollable.scrollTop = scrollable.scrollHeight;
                    }""", dialog.element_handle())
                else:
                    # Scroll window
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                
                page.wait_for_timeout(delay_seconds * 1000)
                
                # Fast check if new reviews loaded
                html = page.content()
                soup = BeautifulSoup(html, "lxml")
                
                # Find review containers. In modern Play Store, reviews are often in a div with a specific structure.
                # We can look for divs that contain star ratings and a date.
                # A common pattern is divs containing a header with user name, stars, date, and body text.
                current_reviews = soup.find_all("div", attrs={"class": "RHo1pe"}) # Example class often used, fallback if not
                if not current_reviews:
                    current_reviews = soup.find_all("div", attrs={"jscontroller": "H6eOGe"}) # Another common wrapper
                
                if not current_reviews:
                    # Fallback broad selector
                    current_reviews = [d for d in soup.find_all("div") if d.find("div", role="img") and d.find("span", text=re.compile(r"^\d{1,2} [A-Z][a-z]+ \d{4}$"))]

                current_count = len(current_reviews)
                
                if current_count >= max_reviews:
                    break
                if current_count == previous_review_count:
                    # Might need an extra scroll or we hit the end
                    scroll_attempts += 1
                    if scroll_attempts > 2:
                        break
                else:
                    scroll_attempts = 0
                
                previous_review_count = current_count

            # Final parse
            html = page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # We need robust extractors since class names change
            # Reviews often have a user name, star rating (role="img", aria-label="Rated X stars out of five"), date, and text.
            
            review_divs = []
            
            # Attempt 1: Known classes
            for div in soup.find_all("div"):
                if div.has_attr("jscontroller") and "H6eOGe" in div["jscontroller"]:
                    review_divs.append(div)
                elif div.has_attr("class") and "RHo1pe" in div["class"]:
                    review_divs.append(div)
            
            # Remove duplicates by walking up/down
            # If not found, use heuristic: div with star rating img + text
            if not review_divs:
                for img in soup.find_all("div", role="img"):
                    if img.has_attr("aria-label") and "Rated" in img["aria-label"] and "stars" in img["aria-label"]:
                        # This is a star rating. The review container is likely a parent.
                        parent = img.find_parent("div", limit=5) # don't go too high
                        if parent:
                            review_divs.append(parent)
            
            # Deduplicate by looking at actual text content
            seen_texts = set()

            for div in review_divs:
                if len(records) >= max_reviews:
                    break

                try:
                    # Rating
                    rating = None
                    star_elem = div.find(lambda tag: tag.name == "div" and tag.has_attr("aria-label") and "Rated" in tag["aria-label"])
                    if star_elem:
                        match = re.search(r"Rated (\d(?:\.\d)?)", star_elem["aria-label"])
                        if match:
                            rating = float(match.group(1))
                    
                    if rating is None:
                        continue # Not a valid review block

                    # Text
                    # Usually the text is in a div with a specific class, or it's the longest text block.
                    text = ""
                    # Often there's a div with class "h3YV2d"
                    text_div = div.find("div", class_="h3YV2d")
                    if text_div:
                        text = text_div.get_text(separator=" ", strip=True)
                    else:
                        # Fallback: get all text, try to remove headers
                        text = div.get_text(separator=" ", strip=True)
                        # This fallback is messy, so we prioritize finding specific spans
                    
                    if not text or text in seen_texts:
                        continue
                    seen_texts.add(text)

                    # Date
                    date_pub = None
                    # Date is often in a span like "October 12, 2023"
                    date_span = div.find("span", text=re.compile(r"^[A-Z][a-z]+ \d{1,2}, \d{4}$"))
                    if date_span:
                        date_pub = date_span.get_text(strip=True)

                    # Reviewer name
                    reviewer = ""
                    name_div = div.find("div", class_="X5PpBb")
                    if name_div:
                        reviewer = name_div.get_text(strip=True)
                    
                    # Engagement (Helpful count)
                    helpful_count = 0
                    helpful_div = div.find("div", text=re.compile(r"^\d+ people found this helpful$"))
                    if helpful_div:
                        match = re.search(r"^(\d+)", helpful_div.get_text(strip=True))
                        if match:
                            helpful_count = int(match.group(1))

                    records.append(RawRecord(
                        record_id=self.make_record_id(),
                        source_type="play_store",
                        platform=platform,
                        original_url=url,
                        raw_text=text,
                        date_published=self._parse_date(date_pub),
                        date_scraped=datetime.now(timezone.utc).isoformat(),
                        rating=rating,
                        engagement={"thumbs_up": helpful_count} if helpful_count > 0 else None,
                        language="en",
                        metadata={
                            "app_id": app_id,
                            "reviewer_name": reviewer,
                        },
                    ))

                except Exception as e:
                    print(f"    Error parsing Play Store review: {e}")

            print(f"    Scraped {len(records)} reviews for {app_id}")

        except Exception as e:
            print(f"    Playwright error for {app_id}: {e}")
            traceback.print_exc()
        finally:
            if browser:
                browser.close()

        return records

    def scrape(self) -> ScrapeResult:
        config = GOOGLE_PLAY_CONFIG
        all_records = []
        errors = 0

        print(f"[google_play] Starting scrape of {len(config['apps'])} apps...")

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                for app_config in config["apps"]:
                    app_id = app_config["app_id"]
                    platform = app_config["platform"]
                    
                    try:
                        records = self._scrape_app(p, app_id, platform, config["max_reviews_per_app"], config["delay_seconds"])
                        all_records.extend(records)
                    except Exception as e:
                        print(f"  ERROR scraping {app_id}: {e}")
                        errors += 1
                        
                    self.safe_delay(config["delay_seconds"])
        except Exception as e:
             print(f"  FATAL Playwright error: {e}")
             errors += 1

        result = ScrapeResult(
            scraper="google_play",
            scraped_at=datetime.now(timezone.utc).isoformat(),
            config_snapshot={
                "apps": [a["app_id"] for a in config["apps"]],
                "max_reviews_per_app": config["max_reviews_per_app"],
                "delay_seconds": config["delay_seconds"]
            },
            stats={
                "total_fetched": len(all_records),
                "errors": errors,
            },
            records=all_records,
        )

        print(f"\n[google_play] Done: {len(all_records)} total records, {errors} errors")
        return result


if __name__ == "__main__":
    scraper = GooglePlayScraper()
    filepath = scraper.run()
    print(f"\nOutput: {filepath}")
