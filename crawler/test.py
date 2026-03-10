from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect
from typing import List, Dict
import json
import csv
from datetime import datetime

def expand_all_read_more(page) -> int:
    """Click all exact 'Read more' buttons."""
    buttons = page.get_by_role("button").filter(has_text="Read more")
    count = buttons.count()
    print(f"🔍 Found {count} 'Read more' buttons")
    
    expanded = 0
    for i in range(count):
        try:
            buttons.nth(i).scroll_into_view_if_needed()
            buttons.nth(i).click(timeout=5000)
            page.wait_for_timeout(1500)
            expanded += 1
        except PlaywrightTimeoutError:
            return False
    return expanded

def collect_reviews(page) -> List[str]:
    """Expand all, then collect .K7oBsc reviews."""
    # Step 1: Expand
    expand_all_read_more(page)
    
    # Step 2: Collect
    review_elements = page.locator('.STQFb.eoY5cb .K7oBsc')
    # containers = page.locator('.jftiEf, .WIwmTb, [data-review-id]')
    reviews = []
    for i in range(review_elements.count()):
        text = review_elements.nth(i).inner_text().strip()
        if text:
            reviews.append(text)
    
    return reviews

# SCROLLING
def get_scroll_height(page) -> int:
    return page.evaluate("() => document.body.scrollHeight")  # [web:16]


def scroll_up_tiny(page, px=200, pause_ms=150):
    page.mouse.wheel(0, -abs(px))  # negative deltaY scrolls up [web:4]
    page.wait_for_timeout(pause_ms)


def scroll_down_step(page, px=1000, pause_ms=150):
    page.mouse.wheel(0, abs(px))  # positive deltaY scrolls down [web:4]
    page.wait_for_timeout(pause_ms)


def scroll_until_end(
    page,
    step_px=1000,
    pause_ms=250,
    rescue_up_px=200,
    max_no_growth=3,
    end_selector: str | None = None,
):
    page.wait_for_selector("body")

    no_growth = 0
    last_h = get_scroll_height(page)

    while True:
        if end_selector and page.locator(end_selector).first.is_visible():
            print("finished")
            return

        scroll_down_step(page, px=step_px, pause_ms=pause_ms)
        h1 = get_scroll_height(page)

        if h1 > last_h:
            last_h = h1
            no_growth = 0
            continue

        # No growth after scrolling down -> try tiny scroll up once, then down again
        scroll_up_tiny(page, px=rescue_up_px, pause_ms=pause_ms)
        scroll_down_step(page, px=step_px, pause_ms=pause_ms)
        h2 = get_scroll_height(page)

        if h2 > last_h:
            last_h = h2
            no_growth = 0
            continue

        no_growth += 1
        if no_growth >= max_no_growth:
            print("finished")
            return

if __name__ == "__main__":
    link ='https://www.google.com/travel/search?q=hotels&gsas=1&qs=MiZDaGdJOTlDOHk1ZXM3SXlfQVJvTEwyY3ZNWFJtYWpNNWNIRVFBUTgNSAA&ts=CAEaRwonEiU6I0N1bWJlcmxhbmQgQ2l0eSBDb3VuY2lsLCBTeWRuZXkgTlNXEhwSFAoHCOoPEAQYBhIHCOoPEAQYBxgBMgQIABAAKgcKBToDQVVE&ap=MAC6AQdyZXZpZXdz&ved=0CAAQ5JsGahcKEwjY9pHvro-TAxUAAAAAHQAAAAAQBA'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Go to page + open reviews
        page.goto(link, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # CHECK BUTTONS
        scroll_until_end(page)
        review = collect_reviews(page)
        print(review)
        
        print("✅ Done!")
        page.wait_for_timeout(5000)
        browser.close()