import sys
import asyncio
from pathlib import Path
import pandas as pd

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
    collect_reviews,
)

st.title("Google Travel Hotel Scraper")

query = st.text_input("Enter search keyword", value="hotels")

# Session state
if "hotels" not in st.session_state:
    st.session_state.hotels = {}  # {name: url}
if "reviews" not in st.session_state:
    st.session_state.reviews = []
if "chosen_hotel" not in st.session_state:
    st.session_state.chosen_hotel = None

def fetch_reviews():
    """Fetch reviews for selected hotel."""
    chosen = st.session_state.chosen_hotel
    if not chosen:
        return
    url = st.session_state.hotels.get(chosen)
    if not url:
        st.error("No URL for selected hotel.")
        return

    with st.spinner(f"Collecting reviews for {chosen}..."):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()

                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)  # let page load

                reviews = collect_reviews(page, url)  # your function

                context.close()
                browser.close()

            st.session_state.reviews = reviews
            st.rerun()  # refresh to show results
        except Exception as e:
            st.error(f"Error collecting reviews: {str(e)}")

if st.button("Search and Collect"):
    if not query.strip():
        st.warning("Please enter a keyword.")
    else:
        with st.spinner("Launching browser and scraping..."):
            hotels = {}

            try:
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

                    hotel_urls = collect_hotel_urls_from_results(page, limit=None)

                    for url in hotel_urls:
                        name = collect_hotel_name(page, url)
                        if name:
                            hotels[name] = url

                    context.close()
                    browser.close()
            except Exception as e:
                st.error(f"Search error: {str(e)}")

            st.session_state.hotels = hotels
            st.session_state.reviews = []
            st.session_state.chosen_hotel = None

st.write(f"Found {len(st.session_state.hotels)} hotels")

if st.session_state.hotels:
    hotel_names = list(st.session_state.hotels.keys())
    
    st.selectbox(
        "Pick a hotel from results",
        hotel_names,
        index=hotel_names.index(st.session_state.chosen_hotel) if st.session_state.chosen_hotel in hotel_names else 0,
        key="chosen_hotel",
        on_change=fetch_reviews,
    )

    chosen = st.session_state.chosen_hotel
    if chosen:
        st.success(f"Selected: {chosen}")

# Display reviews
if st.session_state.reviews:
    st.write(f"Collected {len(st.session_state.reviews)} reviews")
    
    if isinstance(st.session_state.reviews[0], dict):
        df = pd.DataFrame(st.session_state.reviews)
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download reviews as CSV",
            data=csv,
            file_name=f"{chosen}_reviews.csv",
            mime="text/csv",
        )
    else:
        st.write(st.session_state.reviews[:10])  # list fallback
