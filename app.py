import streamlit as st
import pandas as pd
from utils import fetch_reddit_posts, analyse_pain_points
import time

# ============================================================
# PAGE CONFIGURATION (The Foundation)
# ============================================================
st.set_page_config(
    page_title="Curiosity Radar — Discover what to build",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="expanded" # Gives the app a SaaS feel
)

# Minimal CSS to hide Streamlit watermarks
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if "results" not in st.session_state: st.session_state.results = None
if "last_keyword" not in st.session_state: st.session_state.last_keyword = ""
if "post_count" not in st.session_state: st.session_state.post_count = 0
if "pending_kw" not in st.session_state: st.session_state.pending_kw = ""

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# ============================================================
# SIDEBAR (Global Navigation)
# ============================================================
# ============================================================
# SIDEBAR (Global Navigation)
# ============================================================
with st.sidebar:
    # 1. WORKSPACE HEADER
    col1, col2 = st.columns([1, 4])
    with col1:
        # Calling your newly uploaded logo file!
        st.image("assets/logo.png", width=40)
    with col2:
        st.markdown("**Builder Workspace**")
        st.caption("Free Tier")
        
    st.divider()

    # 2. RECENT HISTORY
    st.markdown("<p style='font-size: 0.8rem; font-weight: 600; color: #7A7A9A; text-transform: uppercase;'>Recent Scans</p>", unsafe_allow_html=True)
    
    st.button("🕒 Sourdough baking", use_container_width=True, type="secondary")
    st.button("🕒 D&D 5e campaigns", use_container_width=True, type="secondary")
    st.button("🕒 Marathon prep", use_container_width=True, type="secondary")
    
    st.divider()

    # 3. SETTINGS & CONFIGURATION
    st.markdown("<p style='font-size: 0.8rem; font-weight: 600; color: #7A7A9A; text-transform: uppercase;'>Engine Settings</p>", unsafe_allow_html=True)
    
    api_key_input = st.text_input("Gemini API Key", type="password", help="Stored locally in your browser session.")
    st.slider("Subreddits to Scan", min_value=1, max_value=5, value=3, help="Higher depth takes longer to process.")

    st.divider()
    
    # 4. PREMIUM UPSELL
    with st.container():
        st.markdown("🚀 **Upgrade to Pro**")
        st.caption("Unlock competitor analysis, CSV exports, and API access.")
        st.button("View Plans", type="primary", use_container_width=True)

# ============================================================
# MAIN INTERFACE (Hero & Search)
# ============================================================
st.markdown("<h1 style='text-align: center;'>Find your next micro-SaaS idea.</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #7A7A9A; margin-bottom: 2rem;'>Type a hobby, industry, or task to reveal what people actually want built.</p>", unsafe_allow_html=True)

# Search Grid Layout
col1, col2 = st.columns([3, 1])

with col1:
    keyword = st.text_input(
        "Search Topic",
        value=st.session_state["pending_kw"],
        placeholder="e.g., marathon training, remote work, sourdough...",
        label_visibility="collapsed"
    )
with col2:
    scan_clicked = st.button("Scan Radar 🎯", type="primary", use_container_width=True)

# Example Search Pills (Using Columns for clean layout)
st.caption("Try a popular niche:")
ex_col1, ex_col2, ex_col3, ex_col4 = st.columns(4)
examples = [("🏃 Marathons", "marathon training"), ("🍞 Baking", "sourdough baking"), ("🪴 Plants", "indoor plant care"), ("💸 Finance", "personal finance")]

for col, (label, search_term) in zip([ex_col1, ex_col2, ex_col3, ex_col4], examples):
    with col:
        if st.button(label, use_container_width=True):
            keyword = search_term
            scan_clicked = True

# ============================================================
# DYNAMIC INTERACTIVITY (The "Alive" State)
# ============================================================
if scan_clicked and keyword:
    if not API_KEY:
        st.error("Missing GEMINI_API_KEY in secrets.")
    else:
        # Create an empty container to hold our dynamic loading messages
        status_container = st.empty()
        
        with status_container.container():
            with status_container.container():
            # Add your loading video here!
            st.video("assets/radar_loop.mp4", autoplay=True, loop=True)
            st.info(f"📡 Calibrating radar for '{keyword}'...")
            
            # Fetch Posts
            posts = fetch_reddit_posts(keyword)
            
            if posts:
                # Update the UI dynamically to show progress
                status_container.warning(f"🔍 Reading {len(posts)} recent complaints...")
                
                # Fetch AI Analysis
                results = analyse_pain_points(keyword, posts, API_KEY)
                
                if results:
                    st.session_state.results = sorted(results, key=lambda x: x.get("opportunity_score", 0), reverse=True)
                    st.session_state.last_keyword = keyword
                    st.session_state.post_count = len(posts)
                    
                    status_container.success("✨ Analysis complete!")
                    time.sleep(0.5) # Let the user read the success message
                    
        # Clear the loading messages to make room for results
        status_container.empty()

# ============================================================
# RESULTS FEED (Progressive Disclosure)
# ============================================================
if st.session_state.results is not None:
    if len(st.session_state.results) == 0:
        # Add your empty state illustration here!
        st.image("assets/empty_state.png", use_column_width=True)
        st.info("🤔 No clear pain points found. Try a broader search term.")
    else:
        st.divider()
        st.subheader(f"Top opportunities for: {st.session_state.last_keyword}")
        
        for i, item in enumerate(st.session_state.results):
            # Create visual hierarchy
            with st.container():
                st.markdown(f"### #{i+1} {item['pain_point']}")
                st.write(item['description'])
                
                # Metric display using columns
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Demand Score", f"{item['demand_score']}/10")
                m_col2.metric("Difficulty to Build", f"{item['difficulty_score']}/10")
                m_col3.metric("Opportunity Rating", f"{item['opportunity_score']}/10")
                
                st.success(f"💡 **App Idea:** {item['app_idea']}")
                
                # Progressive Disclosure: Hide the raw data until requested
                with st.expander("View Raw Reddit Evidence"):
                    st.caption(f"\"{item['evidence']}\"")
                
                st.markdown("<br>", unsafe_allow_html=True) # Spacing between cards
