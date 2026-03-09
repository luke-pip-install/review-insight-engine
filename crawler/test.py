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
    review_elements = page.locator('.K7oBsc')
    reviews = []
    for i in range(review_elements.count()):
        text = review_elements.nth(i).inner_text().strip()
        if text:
            reviews.append(text)
    
    return reviews

if __name__ == "__main__":
    link ='https://www.google.com/travel/search?q=hotels&gsas=1&qs=MiZDaGdJOTlDOHk1ZXM3SXlfQVJvTEwyY3ZNWFJtYWpNNWNIRVFBUTgNSAA&ts=CAEaRwonEiU6I0N1bWJlcmxhbmQgQ2l0eSBDb3VuY2lsLCBTeWRuZXkgTlNXEhwSFAoHCOoPEAQYBhIHCOoPEAQYBxgBMgQIABAAKgcKBToDQVVE&ap=MAC6AQdyZXZpZXdz&ved=0CAAQ5JsGahcKEwjY9pHvro-TAxUAAAAAHQAAAAAQBA'

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Go to page + open reviews
        page.goto(link, wait_until="networkidle")
        page.wait_for_timeout(3000)

        # CHECK BUTTONS
        review = collect_reviews(page)
        print(review)
        
        print("✅ Done!")
        page.wait_for_timeout(10000)
        browser.close()