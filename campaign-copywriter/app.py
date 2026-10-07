"""
app.py  -  THE SCREEN YOU SEE
=============================

Streamlit turns this Python file into a web page with buttons.
Every time you click something, Streamlit re-runs this file from top to
bottom and redraws the page. That's why we keep results in
st.session_state ("the app's short-term memory") - otherwise they would
vanish on the next click.

The page, top to bottom:
1. Sidebar: brand name, tone, creativity (temperature)
2. Step 1: upload a customer CSV (or use the sample)
3. Step 2: see the segments
4. Step 3: describe the product and offer, click Generate
5. Results: one email per segment + download buttons
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from llm import AIError, get_api_key
from segmenter import add_segments, load_customers, summarise_segments
from writer import BadAIAnswer, write_email_for_segment

SAMPLE_FILE = Path(__file__).parent / "sample_customers.csv"

st.set_page_config(page_title="AI Campaign Copywriter", page_icon="✉️", layout="wide")
st.title("AI Campaign Copywriter")
st.caption("Upload customers → AI sorts them into groups → writes a personalised email for each group.")

# ---------------------------------------------------------------- API key check
try:
    get_api_key()
except AIError as problem:
    st.error(str(problem))
    st.stop()          # nothing else works without a key, so stop drawing the page

# ---------------------------------------------------------------- 1. Sidebar settings
with st.sidebar:
    st.header("Brand settings")
    brand_name = st.text_input("Brand name", value="Noor Fashion")
    tone = st.selectbox(
        "Tone of voice",
        ["warm and elegant", "playful and energetic", "premium and minimal",
         "friendly and straightforward"],
    )
    temperature = st.slider(
        "Creativity (temperature)", 0.0, 1.0, 0.7, 0.1,
        help="0 = predictable, same answer every time. 1 = more creative and varied.",
    )

# ---------------------------------------------------------------- 2. Load customers
st.subheader("Step 1 · Customers")
uploaded = st.file_uploader("Upload a customer CSV", type="csv")
use_sample = st.checkbox("Use the sample customer list instead", value=uploaded is None)

source = uploaded if uploaded is not None and not use_sample else SAMPLE_FILE
try:
    customers = add_segments(load_customers(source))
except ValueError as problem:
    st.error(str(problem))
    st.stop()

with st.expander(f"See all {len(customers)} customers"):
    st.dataframe(customers, width="stretch", hide_index=True)

# ---------------------------------------------------------------- 3. Segments
st.subheader("Step 2 · Segments")
summary = summarise_segments(customers)
st.dataframe(summary, width="stretch", hide_index=True)

# ---------------------------------------------------------------- 4. Campaign brief
st.subheader("Step 3 · Campaign brief")
col1, col2 = st.columns(2)
product = col1.text_input("Product", value="New Eid collection: hand-embroidered linen kaftans")
offer = col2.text_input("Offer", value="20% off for 7 days, free delivery across the UAE")

if st.button("Generate emails", type="primary"):
    st.session_state["emails"] = []
    st.session_state["usage"] = []
    progress = st.progress(0.0, text="Starting...")

    segments = summary.to_dict("records")       # one dictionary per segment
    for number, stats in enumerate(segments, start=1):
        progress.progress((number - 1) / len(segments), text=f"Writing the {stats['segment']} email...")
        try:
            email, usage = write_email_for_segment(
                stats["segment"], stats, product, offer, brand_name, tone, temperature
            )
            st.session_state["emails"].append(email)
            st.session_state["usage"].append(usage)
        except (AIError, BadAIAnswer) as problem:
            st.error(f"{stats['segment']}: {problem}")
            break
    progress.progress(1.0, text="Done")

# ---------------------------------------------------------------- 5. Results
emails = st.session_state.get("emails", [])
if emails:
    st.subheader("Your campaign")

    usage = st.session_state["usage"]
    tokens_in = sum(u["input_tokens"] for u in usage)
    tokens_out = sum(u["output_tokens"] for u in usage)
    m1, m2, m3 = st.columns(3)
    m1.metric("Emails written", len(emails))
    m2.metric("Tokens sent (input)", f"{tokens_in:,}")
    m3.metric("Tokens received (output)", f"{tokens_out:,}")
    st.caption(f"Model: {usage[-1]['model']} · Free tier, so this run cost nothing.")

    for email in emails:
        with st.container(border=True):
            st.markdown(f"**{email['segment']}**")
            st.markdown(f"**Subject:** {email['subject']}")
            st.markdown(f"*{email['preview_text']}*")
            st.write(email["body"])
            st.markdown(f"**Button:** {email['cta']}")
            if email.get("why_this_works"):
                st.caption("Why this works: " + email["why_this_works"])

    d1, d2 = st.columns(2)
    d1.download_button("Download as JSON", json.dumps(emails, indent=2, ensure_ascii=False),
                       file_name="campaign.json", mime="application/json")
    d2.download_button("Download as CSV", pd.DataFrame(emails).to_csv(index=False),
                       file_name="campaign.csv", mime="text/csv")
