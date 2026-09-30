"""
app.py

Streamlit front-end for the Indian Tourism LLM Assistant.
Run from the project root with:
    streamlit run app.py
"""

import os
import streamlit as st

from src.data_loader import load_dataset, DatasetError
from src.search import search_destinations, format_record_summary
from src.llm_client import ask_tourism_assistant, LLMError

DATA_PATH = os.path.join("data", "india_tourism_dataset.json")

st.set_page_config(page_title="Indian Tourism LLM Assistant", page_icon="🧳")

st.title("🧳 Indian Tourism LLM Assistant")
st.write(
    "Ask about destinations, budgets, seasons, or trip ideas across India. "
    "Answers are grounded in a 100-destination dataset - verify real-world "
    "details before you travel."
)

# --- Load dataset once, cached across reruns ---
@st.cache_data
def get_records():
    return load_dataset(DATA_PATH)


try:
    records = get_records()
except DatasetError as e:
    st.error(f"Could not load the dataset: {e}")
    st.stop()

# --- Sidebar filters ---
st.sidebar.header("Filters (optional)")

all_states = sorted({r.get("state") for r in records if r.get("state")})
all_regions = sorted({r.get("region") for r in records if r.get("region")})
all_trip_types = sorted({t for r in records for t in r.get("trip_types", [])})

state_filter = st.sidebar.selectbox("State", ["Any"] + all_states)
region_filter = st.sidebar.selectbox("Region", ["Any"] + all_regions)
trip_type_filter = st.sidebar.selectbox("Trip type", ["Any"] + all_trip_types)
duration_filter = st.sidebar.slider("Trip duration (days)", 1, 15, 4)
budget_tier_filter = st.sidebar.selectbox(
    "Budget tier", ["budget_category", "mid_range_category", "luxury_category"]
)
max_daily_budget = st.sidebar.number_input(
    "Max daily budget (INR, optional)", min_value=0, value=0, step=500
)

if st.sidebar.button("Reset filters"):
    st.rerun()

# --- Main input ---
user_question = st.text_input(
    "What would you like to plan?",
    placeholder="e.g. Suggest a 4-day budget beach trip for a couple",
)

if st.button("Get suggestions") and user_question:
    with st.spinner("Searching the dataset and asking the assistant..."):
        matches = search_destinations(
            records,
            keyword=user_question,
            state=None if state_filter == "Any" else state_filter,
            region=None if region_filter == "Any" else region_filter,
            trip_type=None if trip_type_filter == "Any" else trip_type_filter,
            duration_days=duration_filter,
            budget_tier=budget_tier_filter,
            max_daily_budget=max_daily_budget or None,
        )

        if not matches:
            st.warning(
                "No matching destinations found in the dataset for these filters. "
                "Try loosening a filter or rephrasing your question."
            )
        else:
            st.subheader(f"Matched {len(matches)} destination(s) from the dataset")
            for m in matches[:5]:
                st.markdown(format_record_summary(m))

            summary_text = "\n".join(format_record_summary(r) for r in matches[:5])

            try:
                answer = ask_tourism_assistant(user_question, summary_text)
                st.subheader("Assistant's answer")
                st.write(answer)
            except LLMError as e:
                st.error(f"Assistant error: {e}")
