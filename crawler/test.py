from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect


GOOGLE_TRAVEL = "https://www.google.com/travel"
SEARCHBOX_NAME = "Search for flights, hotels and more"
HOTEL_LINKS_SELECTOR = "a.PVOOXe"
REVIEWS_TAB_ROLE_NAME = "Reviews"


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

# def collect_hotel_urls_from_results(page, limit: int = 30) -> list[str]:
#     # # Scroll results page so more cards load (if infinite scroll)
#     # scroll_to_end(page, pause_ms=800, max_steps=60, stable_rounds=3)

#     # Re-grab after scrolling (DOM likely changed)
#     cards = page.locator(HOTEL_LINKS_SELECTOR)
#     expect(cards.first).to_be_visible()

#     hrefs = cards.evaluate_all(
#         "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
#     )

#     urls = [urljoin(page.url, h) for h in hrefs]
#     urls = list(dict.fromkeys(urls))
#     return urls[:limit]

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

def open_reviews_on_hotel_page(page, hotel_url: str) -> tuple[bool, str | None]:
    page.goto(hotel_url, wait_until="domcontentloaded")

    # Get hotel name
    name_locator = page.locator(".FNkAEc.o4k8l")
    hotel_name = None

    try:
        expect(name_locator.first).to_be_visible(timeout=10_000)
        hotel_name = name_locator.first.inner_text().strip()
    except PlaywrightTimeoutError:
        print("Hotel name not found")

    reviews_tab = page.locator("div[role='tab']#reviews")

    try:
        expect(reviews_tab).to_be_visible(timeout=10_000)
        reviews_tab.click()
        page.wait_for_timeout(800)

        reached_end = scroll_until_end(
            page,
            end_selector="text=/end of results|no more results/i"
        )

        print("Hotel:", hotel_name)
        print("Scrolled reviews to end:", reached_end)

        return True, hotel_name

    except PlaywrightTimeoutError:
        return False, hotel_name

# def open_reviews_on_hotel_page(page, hotel_url: str) -> bool:
#     page.goto(hotel_url, wait_until="domcontentloaded")  # valid wait_until options include domcontentloaded [web:104]

#     # Prefer role-based locator for the Reviews tab [web:82]
#     # reviews_tab = page.get_by_role("tab", name=REVIEWS_TAB_ROLE_NAME)
#     reviews_tab = page.locator("div[role='tab']#reviews")

#     try:
#         expect(reviews_tab).to_be_visible(timeout=10_000)
#         reviews_tab.click()
#         return True
#     except PlaywrightTimeoutError:
#         return False


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



with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # 1) Go to Google Travel and search "hotels"
    page.goto(GOOGLE_TRAVEL, wait_until="domcontentloaded")  # [web:104]

    search = page.get_by_role("combobox", name=SEARCHBOX_NAME)
    search.wait_for(state="visible")
    search.click()
    search.fill("hotels")
    page.wait_for_timeout(1000)
    search.press("Enter")
    page.wait_for_timeout(2000)

    # 2) Collect hotel URLs from the results list
    hotel_urls = collect_hotel_urls_from_results(page, limit=30)
    print(f"Collected {len(hotel_urls)} hotel URLs")

    # 3) Visit each hotel URL and click the Reviews tab
    # ok = 0
    # for i, url in enumerate(hotel_urls, start=1):
    #     success = open_reviews_on_hotel_page(page, url)
        
    #     print(f"[{i}/{len(hotel_urls)}] Reviews click={'OK' if success else 'FAILED'} | {url}")
    #     ok += int(success)

    # print(f"Done. Reviews clicked successfully on {ok}/{len(hotel_urls)} pages.")

    context.close()
    browser.close()
