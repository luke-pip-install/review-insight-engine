from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect
from typing import Dict, Optional, List

GOOGLE_TRAVEL = "https://www.google.com/travel"
SEARCHBOX_NAME = "Search for flights, hotels and more"
HOTEL_LINKS_SELECTOR = "a.PVOOXe"

import random
from typing import Optional, Dict

USER_AGENTS = [
    # Desktop & mobile examples – expand this list
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
]

PROXIES = [
    # Playwright proxy format
    # {"server": "http://user:pass@host1:port"},
    # {"server": "http://user:pass@host2:port"},
]

COOKIES_POOLS = [
    # Example cookie sets for google.com
    [
        {"name": "CONSENT", "value": "YES+...", "domain": ".google.com", "path": "/"},
    ],
    [
        {"name": "CONSENT", "value": "YES+2025...", "domain": ".google.com", "path": "/"},
    ],
]

def build_rotated_context(
    browser,
    base_url: str = "https://www.google.com",
    extra_headers: Optional[Dict[str, str]] = None,
):
    ua = random.choice(USER_AGENTS)
    cookies = random.choice(COOKIES_POOLS) if COOKIES_POOLS else []
    proxy = random.choice(PROXIES) if PROXIES else None

    context_kwargs: Dict = {
        "user_agent": ua,
        "extra_http_headers": extra_headers or {},
        "ignore_https_errors": False,
    }

    if proxy:
        context_kwargs["proxy"] = proxy  # Playwright native proxy setting[web:13]

    context = browser.new_context(**context_kwargs)

    if cookies:
        context.add_cookies(cookies)  # Preload session/csrf/consent cookies[web:8]

    page = context.new_page()
    return context, page


def collect_hotel_urls_from_results(page, limit: int = 30) -> list[str]:
    # Wait until results show up
    cards = page.locator(HOTEL_LINKS_SELECTOR)
    expect(cards.first).to_be_visible()

    # scroll_to_end(page, pause_ms=800, max_steps=60, stable_rounds=3)

    # Extract href attributes (often relative)
    hrefs = cards.evaluate_all(
        "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
    )

    # Convert to absolute URLs
    urls = [urljoin(page.url, h) for h in hrefs]
    # Deduplicate while preserving order
    urls = list(dict.fromkeys(urls))
    return urls[:limit]

def open_reviews_on_hotel_page(page, hotel_url: str) -> bool:
    page.goto(hotel_url, wait_until="domcontentloaded")

    reviews_tab = page.locator("div[role='tab']#reviews")
    try:
        expect(reviews_tab).to_be_visible(timeout=10_000)
        reviews_tab.click()

        # (Optional) wait for the reviews panel to appear before scrolling
        page.wait_for_timeout(800)

        reached_end = scroll_until_end(page, end_selector="text=/end of results|no more results/i")
        print("Scrolled reviews to end:", reached_end)
        return True
    except PlaywrightTimeoutError:
        return False

def collect_hotel_name(page, url: str) -> Optional[str]:
    page.goto(url, wait_until="domcontentloaded")
    # name_locator = page.locator(".QORQHb.fZscne").first
    name_locator = page.get_by_role("heading").first

    try:
        expect(name_locator).to_be_visible(timeout=10_000)
        return name_locator.inner_text().strip()
    except PlaywrightTimeoutError:
        return None

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
def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Initial navigation (optional “warming” context)
        warm_ctx = browser.new_context()
        warm_page = warm_ctx.new_page()
        warm_page.goto(GOOGLE_TRAVEL, wait_until="domcontentloaded")
        search = warm_page.get_by_role("combobox", name=SEARCHBOX_NAME)
        search.wait_for(state="visible")
        search.click()
        search.fill("hotels")
        warm_page.wait_for_timeout(1000)
        search.press("Enter")
        warm_page.wait_for_timeout(2000)

        hotel_urls = collect_hotel_urls_from_results(warm_page, limit=30)
        warm_ctx.close()

        hotel_names = []

        for url in hotel_urls:
            ctx, page = build_rotated_context(
                browser,
                base_url="https://www.google.com",
                extra_headers={
                    "Accept-Language": random.choice(
                        ["en-US,en;q=0.9", "en-AU,en;q=0.8", "en-GB,en;q=0.8"]
                    ),
                },
            )
            try:
                name = collect_hotel_name(page, url)
                print(url, name)
                hotel_names.append(name)
                # ok = open_reviews_on_hotel_page(page, url)
                # if not ok:
                #     print("Could not open reviews tab")
                #     continue

            # for name in hotel_names:
            #     print(name)
            finally:
                ctx.close()

        browser.close()


if __name__ == "__main__": 
    main()