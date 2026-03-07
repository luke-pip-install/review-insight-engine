from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect

GOOGLE_TRAVEL = "https://www.google.com/travel"
SEARCHBOX_NAME = "Search for flights, hotels and more"
HOTEL_LINKS_SELECTOR = "a.PVOOXe"
REVIEWS_TAB_ROLE_NAME = "Reviews"


# ---------- Scrolling helpers (reused) ----------

def get_scroll_height(page) -> int:
    return page.evaluate("() => document.body.scrollHeight")  # [web:16]


def scroll_up_tiny(page, px=200, pause_ms=150):
    page.mouse.wheel(0, -abs(px))  # negative deltaY scrolls up [web:8]
    page.wait_for_timeout(pause_ms)


def scroll_down_step(page, px=1000, pause_ms=150):
    page.mouse.wheel(0, abs(px))  # positive deltaY scrolls down [web:8]
    page.wait_for_timeout(pause_ms)


def scroll_until_end(
    page,
    step_px=1000,
    pause_ms=250,
    rescue_up_px=200,
    max_no_growth=6,
    end_selector: str | None = None,
    max_steps: int = 200,  # hard safety cap to avoid any infinite loop
):
    page.wait_for_selector("body")

    no_growth = 0
    last_h = get_scroll_height(page)

    for _ in range(max_steps):
        if end_selector and page.locator(end_selector).first.is_visible():
            return True

        scroll_down_step(page, px=step_px, pause_ms=pause_ms)
        h1 = get_scroll_height(page)

        if h1 > last_h:
            last_h = h1
            no_growth = 0
            continue

        # No growth -> try tiny scroll up once, then down again
        scroll_up_tiny(page, px=rescue_up_px, pause_ms=pause_ms)
        scroll_down_step(page, px=step_px, pause_ms=pause_ms)
        h2 = get_scroll_height(page)

        if h2 > last_h:
            last_h = h2
            no_growth = 0
            continue

        no_growth += 1
        if no_growth >= max_no_growth:
            return True

    return False  # hit max_steps safety cap


# ---------- Your logic ----------

def collect_hotel_urls_from_results(page, limit: int = 30) -> list[str]:
    cards = page.locator(HOTEL_LINKS_SELECTOR)
    expect(cards.first).to_be_visible()

    # Scroll results page so more cards load (infinite scroll)
    scroll_until_end(
        page,
        step_px=1200,
        pause_ms=350,
        rescue_up_px=200,
        max_no_growth=6,
        end_selector="text=/end of results|no more results/i",
        max_steps=120,
    )

    # Re-grab after scrolling (DOM likely changed)
    cards = page.locator(HOTEL_LINKS_SELECTOR)
    expect(cards.first).to_be_visible()

    hrefs = cards.evaluate_all(
        "els => els.map(e => e.getAttribute('href')).filter(Boolean)"
    )

    urls = [urljoin(page.url, h) for h in hrefs]
    urls = list(dict.fromkeys(urls))
    return urls[:limit]


def open_reviews_on_hotel_page(page, hotel_url: str) -> bool:
    page.goto(hotel_url, wait_until="domcontentloaded")

    reviews_tab = page.locator("div[role='tab']#reviews")
    try:
        expect(reviews_tab).to_be_visible(timeout=10_000)
        reviews_tab.click()

        page.wait_for_timeout(800)

        reached_end = scroll_reviews_section_to_end(page, timeout_ms=30_000)
        print("Scrolled reviews to end:", reached_end)
        return True
    except PlaywrightTimeoutError:
        return False


def scroll_reviews_section_to_end(page, timeout_ms: int = 30_000, step: int = 900) -> bool:
    candidates = [
        page.locator("#reviews[role='tab'] div[style*='overflow']").first,
        page.locator("#reviews[role='tab'] div[style*='overflow-y']").first,
        page.locator("#reviews").locator("xpath=ancestor-or-self::*").locator("div[style*='overflow']").first,
    ]

    container = None
    for c in candidates:
        try:
            if c.count() and c.evaluate("e => e && (e.scrollHeight > e.clientHeight)"):
                container = c
                break
        except Exception:
            pass

    if container is None:
        return False

    try:
        container.hover(timeout=3000)
    except Exception:
        pass

    start = page.evaluate("() => Date.now()")
    last_top = -1
    stable_hits = 0

    while True:
        container.evaluate(f"(e) => e.scrollTop = e.scrollTop + {step}")
        page.wait_for_timeout(600)

        top, sh, ch = container.evaluate("(e) => [e.scrollTop, e.scrollHeight, e.clientHeight]")

        if top == last_top or top + ch >= sh - 2:
            stable_hits += 1
        else:
            stable_hits = 0

        last_top = top

        if stable_hits >= 3:
            return True

        if page.evaluate("() => Date.now()") - start > timeout_ms:
            return False


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    page.goto(GOOGLE_TRAVEL, wait_until="domcontentloaded")

    search = page.get_by_role("combobox", name=SEARCHBOX_NAME)
    search.wait_for(state="visible")
    search.click()
    search.fill("hotels")
    page.wait_for_timeout(1000)
    search.press("Enter")
    page.wait_for_timeout(2000)

    hotel_urls = collect_hotel_urls_from_results(page, limit=30)
    print(f"Collected {len(hotel_urls)} hotel URLs")

    ok = 0
    for i, url in enumerate(hotel_urls, start=1):
        success = open_reviews_on_hotel_page(page, url)
        print(f"[{i}/{len(hotel_urls)}] Reviews click={'OK' if success else 'FAILED'} | {url}")
        ok += int(success)

    print(f"Done. Reviews clicked successfully on {ok}/{len(hotel_urls)} pages.")

    context.close()
    browser.close()
