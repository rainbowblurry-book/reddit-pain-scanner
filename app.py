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
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1516321497487-e288fb19713f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80", use_column_width=True)
    st.title("📡 Curiosity Radar")
    st.markdown("Discover genuine user frustrations on Reddit and turn them into your next product idea.")
    
    st.divider()
    st.markdown("**How it works:**")
    st.markdown("1. Enter a niche\n2. AI reads 40 recent posts\n3. Ranks top opportunities")
    
    st.divider()
    st.caption("Built for indie hackers. Powered by Gemini AI.")

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
