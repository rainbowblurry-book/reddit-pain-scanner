import streamlit as st
import pandas as pd
from utils import fetch_reddit_posts, analyse_pain_points
import time

# ============================================================
# ASSET CONFIGURATION (Change your file names here!)
# ============================================================
LOGO_PATH = "assets/logo.png"
EMPTY_STATE_PATH = "assets/empty_state.png"
LOADING_VIDEO_PATH = "assets/radar_loop.mp4" # Ensure this matches your uploaded assets name exactly

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Curiosity Radar — Discover what to build",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="expanded"
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
if "results" not in st.session_state: 
    st.session_state.results = None
if "last_keyword" not in st.session_state: 
    st.session_state.last_keyword = ""
if "post_count" not in st.session_state: 
    st.session_state.post_count = 0
if "pending_kw" not in st.session_state: 
    st.session_state.pending_kw = ""

API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# ============================================================
# SIDEBAR (Global Navigation)
# ============================================================
with st.sidebar:
   # 1. WORKSPACE HEADER
    # Changing to a 1:1 ratio gives the logo a massive space to expand into
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Boom. Much larger. (You can push this to 150 if you want it massive)
        st.image(LOGO_PATH, width=120)
        
    with col2:
        # Pushing the text down slightly so it aligns with the middle of the big logo
        st.markdown("<div style='padding-top: 15px;'><strong>Builder Workspace</strong><br><span style='font-size: 0.85em; color: #7A7A9A;'>Free Tier</span></div>", unsafe_allow_html=True)
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
search_col1, search_col2 = st.columns([3, 1])

with search_col1:
    keyword = st.text_input(
        "Search Topic",
        value=st.session_state["pending_kw"],
        placeholder="e.g., marathon training, remote work, sourdough...",
        label_visibility="collapsed"
    )
with search_col2:
    scan_clicked = st.button("Scan Radar 🎯", type="primary", use_container_width=True)

# Example Search Pills
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
            st.video(LOADING_VIDEO_PATH, autoplay=True, loop=True)
            st.info(f"📡 Calibrating radar for '{keyword}'...")
            
            # Fetch Posts
            posts = fetch_reddit_posts(keyword)
            
            if posts:
                # Update the UI dynamically to show progress
                status_container.warning(f"🔍 Reading {len(posts)} recent complaints...")
                
                # Fetch AI Analysis
                results = analyse_pain_points(keyword, posts, API_KEY)
                
                if results is not None:
                    st.session_state.results = sorted(results, key=lambda x: x.get("opportunity_score", 0), reverse=True)
                    st.session_state.last_keyword = keyword
                    st.session_state.post_count = len(posts)
                    
                    status_container.success("✨ Analysis complete!")
                    time.sleep(0.5)
                    
        # Clear the loading messages to make room for results
        status_container.empty()

# ============================================================
# RESULTS FEED (Progressive Disclosure)
# ============================================================
if st.session_state.results is not None:
    if len(st.session_state.results) == 0:
        st.image(EMPTY_STATE_PATH, use_column_width=True)
        st.info("🤔 No clear pain points found. Try a broader search term.")
    else:
        st.divider()
        st.subheader(f"Top opportunities for: {st.session_state.last_keyword}")
        
        for i, item in enumerate(st.session_state.results):
            with st.container():
                st.markdown(f"### #{i+1} {item.get('pain_point', 'Unknown')}")
                st.write(item.get('description', ''))
                
                # Metric display using columns
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric("Demand Score", f"{item.get('demand_score', 0)}/10")
                m_col2.metric("Difficulty to Build", f"{item.get('difficulty_score', 0)}/10")
                m_col3.metric("Opportunity Rating", f"{item.get('opportunity_score', 0)}/10")
                
                st.success(f"💡 **App Idea:** {item.get('app_idea', '')}")
                
                # Progressive Disclosure: Hide the raw data until requested
                with st.expander("View Raw Reddit Evidence"):
                    st.caption(f"\"{item.get('evidence', '')}\"")
                
                st.markdown("<br>", unsafe_allow_html=True)
