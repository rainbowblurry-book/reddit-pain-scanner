import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
import time
import re
from google import genai
from google.genai import types

# ============================================================
# 1. PAGE CONFIG & PREMIUM MINIMALIST CSS
# ============================================================
st.set_page_config(
    page_title="Reddit Pain Radar",
    page_icon="🎯",
    layout="centered", # Centered is significantly better for readability
    initial_sidebar_state="collapsed"
)

# This CSS strips away Streamlit's default cruft and enforces a clean, Vercel-like aesthetic.
st.markdown("""
<style>
    /* Hide Streamlit top header and default footer */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Enforce a clean, light background globally */
    .stApp {
        background-color: #FAFAFB;
    }
    
    /* Typography refinements */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #111827;
        -webkit-font-smoothing: antialiased;
    }

    /* Premium Input Field */
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        padding: 0.85rem 1.25rem !important;
        font-size: 1.1rem !important; /* Increased */
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #000000 !important;
        box-shadow: 0 0 0 1px #000000 !important;
    }

    /* Premium Button (Stark Black) */
    .stButton > button[kind="primary"] {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.85rem !important; /* Increased */
        font-size: 1.05rem !important; /* Increased */
        transition: transform 0.1s ease, background-color 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #374151 !important;
        transform: translateY(-1px);
    }

    /* Premium Result Cards */
    .pain-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 2rem; /* Increased padding to balance larger text */
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    .pain-card.top-pick {
        border: 2px solid #111827;
    }

    .card-title {
        font-size: 1.5rem; /* Bumped from 1.25 to 1.5 */
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.75rem;
        margin-top: 0;
        line-height: 1.3;
    }
    
    .card-desc {
        font-size: 1.1rem; /* Bumped from 0.95 to 1.1 */
        color: #4B5563;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }

    .app-solution {
        background-color: #F3F4F6;
        padding: 1.25rem;
        border-radius: 8px;
        margin-bottom: 1.25rem;
        border-left: 4px solid #111827;
    }

    .app-solution-title {
        font-size: 0.85rem; /* Bumped from 0.75 to 0.85 */
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: #6B7280;
        margin-bottom: 0.5rem;
    }

    .app-solution-text {
        font-size: 1.1rem; /* Bumped from 0.95 to 1.1 */
        font-weight: 600;
        color: #111827;
        margin: 0;
        line-height: 1.5;
    }

    .evidence-quote {
        font-size: 1rem; /* Bumped from 0.875 to 1.0 */
        color: #6B7280;
        font-style: italic;
        margin: 0;
        line-height: 1.5;
    }

    /* Metric Pills */
    .metric-container {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    .metric-pill {
        padding: 0.4rem 1rem; /* Increased padding */
        border-radius: 999px;
        font-size: 0.9rem; /* Bumped from 0.75 to 0.9 */
        font-weight: 600;
        background-color: #F3F4F6;
        color: #374151;
        border: 1px solid #E5E7EB;
    }
    .pill-high { background-color: #DCFCE7; color: #166534; border-color: #BBF7D0; }
    .pill-med { background-color: #FEF9C3; color: #854D0E; border-color: #FEF08A; }
    .pill-low { background-color: #FEE2E2; color: #991B1B; border-color: #FECACA; }

    .subtle-footer {
        text-align: center;
        font-size: 0.85rem;
        color: #9CA3AF;
        margin-top: 4rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. STATE MANAGEMENT & API SETUP
# ============================================================
if "results" not in st.session_state:
    st.session_state.results = None
if "last_keyword" not in st.session_state:
    st.session_state.last_keyword = ""

# API Key handling - No more ugly sidebar!
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# ============================================================
# 3. CORE LOGIC (BULLETPROOF JSON ENFORCEMENT)
# ============================================================
def fetch_reddit_posts(keyword, limit=25):
    headers = {"User-Agent": "PainRadar/2.0 (research tool)"}
    url = f"https://www.reddit.com/search.rss?q={keyword}&type=link&sort=new&limit={limit}&t=month"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception as e:
        st.error("Failed to connect to Reddit. They might be rate-limiting. Try again in a minute.")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns) or root.findall(".//item")
    
    seen_titles = set()
    results = []

    for entry in entries[:limit]:
        title = (entry.findtext("atom:title", default="", namespaces=ns) or entry.findtext("title", default="")).strip()
        body = (entry.findtext("atom:content", default="", namespaces=ns) or entry.findtext("description", default=""))
        body = re.sub(r"<[^>]+>", " ", body).strip()
        
        if title in seen_titles or not title:
            continue
        seen_titles.add(title)
        results.append({"title": title, "body": body[:600]})
        time.sleep(0.05)

    return results

def analyse_pain_points(keyword, posts, api_key):
    if not posts: return []
    client = genai.Client(api_key=api_key)
    
    posts_text = "\n".join([f"Title: {p['title']}\nBody: {p['body']}" for p in posts])
    
    prompt = f"""
    Analyze these Reddit posts about "{keyword}". Extract genuine user pain points, frustrations, or unmet needs.
    Posts:
    {posts_text}
    """
    
    # THE CRITICAL FIX: We force the API to return a strict JSON array.
    # No more stripping markdown or risking JSONDecodeErrors.
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "pain_point": {"type": "STRING", "description": "Short name (5-8 words)"},
                            "description": {"type": "STRING", "description": "One sentence explaining the problem"},
                            "demand_score": {"type": "INTEGER", "description": "1 to 10"},
                            "difficulty_score": {"type": "INTEGER", "description": "1 to 10"},
                            "opportunity_score": {"type": "INTEGER", "description": "1 to 10"},
                            "app_idea": {"type": "STRING", "description": "One sentence describing the solution"},
                            "evidence": {"type": "STRING", "description": "A direct quote from the posts"}
                        },
                        "required": ["pain_point", "description", "demand_score", "difficulty_score", "opportunity_score", "app_idea", "evidence"]
                    }
                }
            )
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        return []

# ============================================================
# 4. UI COMPONENTS
# ============================================================
def get_pill_class(score, invert=False):
    # If invert is True (like for Difficulty), a high score is bad (red)
    if invert:
        if score >= 8: return "pill-low"
        if score >= 5: return "pill-med"
        return "pill-high"
    else:
        if score >= 8: return "pill-high"
        if score >= 5: return "pill-med"
        return "pill-low"

# --- HERO SECTION ---
st.markdown("""
<div style="text-align: center; margin-top: 3rem; margin-bottom: 2rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800; letter-spacing: -0.025em; margin-bottom: 0.5rem; color: #111827;">
        Pain Radar
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; max-width: 500px; margin: 0 auto;">
        Discover what people actually want built by analyzing real frustrations on Reddit.
    </p>
</div>
""", unsafe_allow_html=True)

# --- SEARCH BAR ---
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("keyword", placeholder="e.g. sourdough, marathon training, AWS...", label_visibility="collapsed")
with col2:
    scan_clicked = st.button("Scan Reddit", type="primary", use_container_width=True)

# --- MISSING API KEY HANDLING ---
if not API_KEY:
    st.warning("⚠️ No hosted API key found. Please add GEMINI_API_KEY to your Streamlit secrets to run this app.")

# --- EXECUTION ---
if scan_clicked and keyword and API_KEY:
    st.session_state.results = None # Clear old results instantly
    
    with st.spinner("Scraping Reddit and analyzing with Gemini..."):
        posts = fetch_reddit_posts(keyword)
        if posts:
            results = analyse_pain_points(keyword, posts, API_KEY)
            st.session_state.results = sorted(results, key=lambda x: x.get("opportunity_score", 0), reverse=True)
            st.session_state.last_keyword = keyword

# --- RESULTS DISPLAY ---
if st.session_state.results:
    st.markdown(f"<p style='color: #6B7280; font-weight: 600; margin-top: 2rem; margin-bottom: 1rem; font-size: 1.05rem;'>Top opportunities for '{st.session_state.last_keyword}'</p>", unsafe_allow_html=True)
    
    for i, item in enumerate(st.session_state.results):
        is_top = i == 0
        card_class = "pain-card top-pick" if is_top else "pain-card"
        badge = "✨ TOP OPPORTUNITY" if is_top else f"#{i+1}"
        
        # CRITICAL: Do NOT indent the HTML below this line. It must be flush left.
        html_string = f"""
<div class="{card_class}">
<p style="font-size: 0.85rem; font-weight: 700; color: #9CA3AF; margin-bottom: 0.5rem; letter-spacing: 0.05em;">{badge}</p>
<h3 class="card-title">{item['pain_point']}</h3>
<p class="card-desc">{item['description']}</p>
<div class="metric-container">
<span class="metric-pill {get_pill_class(item['demand_score'])}">Demand: {item['demand_score']}/10</span>
<span class="metric-pill {get_pill_class(item['difficulty_score'], invert=True)}">Difficulty: {item['difficulty_score']}/10</span>
<span class="metric-pill {get_pill_class(item['opportunity_score'])}">Overall Score: {item['opportunity_score']}/10</span>
</div>
<div class="app-solution">
<p class="app-solution-title">The Missing Tool</p>
<p class="app-solution-text">{item['app_idea']}</p>
</div>
<p class="evidence-quote">"{item['evidence']}"</p>
</div>
"""
        st.markdown(html_string, unsafe_allow_html=True)

# --- CLEAN FOOTER ---
st.markdown("""
<div class="subtle-footer">
    Built by BlurryRainbow. Powered by Gemini. 
    <br><span style="opacity: 0.5;">(Running on hosted API key)</span>
</div>
""", unsafe_allow_html=True)
