import sys
import asyncio
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


import streamlit as st
from playwright.sync_api import sync_playwright
from crawler.run import (
    GOOGLE_TRAVEL,
    SEARCHBOX_NAME,
    collect_hotel_urls_from_results,
    collect_hotel_name,
)

st.title("Google Travel Hotel Scraper")

query = st.text_input("Enter search keyword", value="hotels")

# Keep results across reruns (button clicks cause reruns)
if "hotel_names" not in st.session_state:
    st.session_state.hotel_names = []

if st.button("Search and Collect"):
    if not query.strip():
        st.warning("Please enter a keyword.")
    else:
        with st.spinner("Launching browser and scraping..."):
            hotel_names = []

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                page.goto(GOOGLE_TRAVEL, wait_until="domcontentloaded")

                search = page.get_by_role("combobox", name=SEARCHBOX_NAME)
                search.wait_for(state="visible")
                search.click()
                search.fill(query)
                page.wait_for_timeout(1000)
                search.press("Enter")
                page.wait_for_timeout(3000)

                # Collect ALL URLs your function can find (no limit)
                hotel_urls = collect_hotel_urls_from_results(page, limit=None)

                for url in hotel_urls:
                    name = collect_hotel_name(page, url)
                    if name:
                        hotel_names.append(name)

                context.close()
                browser.close()

            st.session_state.hotel_names = hotel_names

st.write(f"Found {len(st.session_state.hotel_names)} hotels")

if st.session_state.hotel_names:
    chosen = st.selectbox("Pick a hotel from results", st.session_state.hotel_names)  # dropdown [web:6]
    st.write("Selected:", chosen)
