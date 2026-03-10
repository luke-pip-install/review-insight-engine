import sys
import asyncio
import pandas as pd
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
    collect_reviews,
    scroll_until_end,
    open_reviews_on_hotel_page,
)

st.title("Google Travel Hotel Scraper")

query = st.text_input("Enter search keyword", value="hotels")

# Session state
if "hotels" not in st.session_state:
    st.session_state.hotels = {}  # {name: url}
if "hotel_names" not in st.session_state:
    st.session_state.hotel_names = []
if "reviews" not in st.session_state:
    st.session_state.reviews = []

if st.button("Search and Collect"):
    if not query.strip():
        st.warning("Please enter a keyword.")
    else:
        with st.spinner("Launching browser and scraping..."):
            hotel_data = []

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
                        hotel_data.append((name, url))

                context.close()
                browser.close()

            # Update session state
            st.session_state.hotels = {name: url for name, url in hotel_data}
            st.session_state.hotel_names = list(st.session_state.hotels.keys())

st.write(f"Found {len(st.session_state.hotel_names)} hotels")

if st.session_state.hotel_names:
    chosen_name = st.selectbox("Pick a hotel", st.session_state.hotel_names)
    chosen_url = st.session_state.hotels[chosen_name]
    st.write(f"Selected: {chosen_name}")
    st.write(f"URL: {chosen_url}")

    # if st.button("Collect Reviews"):
    #     with st.spinner("Scraping reviews..."):
    #         with sync_playwright() as p:
    #             browser = p.chromium.launch(headless=False)  # Set True for production
    #             context = browser.new_context()
    #             page = context.new_page()
                
    #             page.goto(chosen_url, wait_until="networkidle")
    #             page.wait_for_timeout(3000)
    #             open_reviews_on_hotel_page(page)
    #             scroll_until_end(page)
    #             reviews_list = collect_reviews(page)
    #             context.close()
    #             browser.close()
    #         st.session_state.reviews = reviews_list
    #         st.rerun()

    if st.button("Collect Reviews"):
        with st.spinner("Scraping reviews..."):
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)  # Set True for production
                context = browser.new_context()
                page = context.new_page()
                
                # Navigate and open reviews tab
                if open_reviews_on_hotel_page(page, chosen_url):
                    page.wait_for_timeout(2000)  # Brief pause after scroll
                    reviews_list = collect_reviews(page)
                else:
                    st.error("Failed to open reviews tab")
                    reviews_list = []
                scroll_until_end(page)   
                context.close()
                browser.close()
            st.session_state.reviews = reviews_list
            st.rerun()


if st.session_state.reviews:
    st.success(f"Collected {len(st.session_state.reviews)} reviews")
    
    # Preview
    st.text_area("Preview (first 5):", "\n\n".join(st.session_state.reviews[:5]), height=200)
    
    # CSV Download
    df = pd.DataFrame({"review": st.session_state.reviews})
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Reviews CSV",
        data=csv,
        file_name=f"{chosen_name.replace(' ', '_')}_reviews.csv",
        mime='text/csv'
    )
