import os
import time
import html
import base64
from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image, ImageChops

from utils import (
    fetch_reddit_posts,
    analyse_pain_points,
    is_daily_cap_reached,
    daily_scans_remaining,
)

# ============================================================
# ASSETS
# ============================================================
LOGO_PATH        = "assets/logo.png"
EMPTY_STATE_PATH = "assets/empty_state.png"

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Curiosity Radar — Find what people want built",
    page_icon="📡",
    layout="centered",
    # initial_sidebar_state="auto",   # ← uncomment when enabling sidebar
    initial_sidebar_state="collapsed",
)

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}

    .stApp { background: #FFFEF9; }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                     Helvetica, Arial, sans-serif;
        color: #1A1A2E;
        -webkit-font-smoothing: antialiased;
    }

    [data-testid="block-container"] {
        max-width: 820px !important;
        padding-top: 0 !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        overflow-x: hidden !important;
    }

    @media (max-width: 768px) {
        [data-testid="block-container"] {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }

    .logo-row {
        display: flex;
        justify-content: center;
        padding-top: 1.25rem;
        margin-bottom: 1.5rem;
    }

    .logo-row img {
        display: block;
        height: 44px;
        width: auto;
    }

    @media (max-width: 768px) {
        .logo-row {
            padding-top: 0.9rem;
            margin-bottom: 1.1rem;
        }
        .logo-row img {
            height: 36px;
        }
    }

    .hero-wrap {
        text-align: center;
        padding: 0 0 1.15rem 0;
    }

    .hero-title {
        margin: 0 0 0.7rem 0;
        font-size: clamp(1.9rem, 5.6vw, 3.15rem);
        line-height: 1.08;
        letter-spacing: -0.04em;
        font-weight: 800;
        color: #17172F;
        text-wrap: balance;
    }

    .hero-subtitle {
        max-width: 590px;
        margin: 0 auto;
        color: #6B6B85;
        font-size: 1.03rem;
        line-height: 1.65;
    }

    .section-divider {
        border: none;
        border-top: 1px solid #EEEBE5;
        margin: 0;
    }

    .section-kicker {
        text-align: center;
        color: #B8B0A4;
        font-size: 0.8rem;
        margin: 1.1rem 0 0.75rem 0;
    }

    .mini-heading {
        text-align: center;
        margin: 0 0 0.2rem 0;
        font-weight: 700;
        color: #1A1A2E;
        font-size: 0.95rem;
    }

    .mini-subheading {
        text-align: center;
        margin: 0 0 0.85rem 0;
        color: #B8B0A4;
        font-size: 0.8rem;
    }

    .steps-row {
        display: flex;
        gap: 1.75rem;
        justify-content: center;
        align-items: flex-start;
        margin: 1.5rem 0 1.75rem 0;
        padding: 0 0.25rem;
    }

    .step-item {
        flex: 1;
        max-width: 200px;
        text-align: center;
    }

    .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #17172F;
        color: #FFFFFF;
        font-size: 0.72rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .step-label {
        margin: 0 0 0.2rem 0;
        font-weight: 700;
        color: #1A1A2E;
        font-size: 0.88rem;
    }

    .step-desc {
        margin: 0;
        color: #8A8A9F;
        font-size: 0.8rem;
        line-height: 1.5;
    }

    @media (max-width: 768px) {
        .steps-row {
            gap: 0.9rem;
            margin: 1.15rem 0 1.4rem 0;
        }
        .step-num {
            width: 24px;
            height: 24px;
            font-size: 0.65rem;
        }
        .step-label {
            font-size: 0.8rem;
        }
        .step-desc {
            font-size: 0.72rem;
        }
    }

    .example-card {
        position: relative;
        background: #FFFFFF;
        border: 1.5px solid #F0EBE3;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        margin-bottom: 1.75rem;
    }

    .example-card.demo {
    background: #F0F4FF;
    border: 1.5px solid #C7D5F8;
    box-shadow: 0 1px 6px rgba(79,108,249,0.06);
}

.example-card.demo .example-tag {
    background: #4F6CF9;
    color: #FFFFFF;
    border: 1px solid #4F6CF9;
}

/* Blue solution box and text inside demo */
.example-card.demo .solution-box {
    background: #E8EEFF;
    border-left: 3px solid #4F6CF9;
}

.example-card.demo .solution-label { color: #2D43B8; }
.example-card.demo .top-opportunity { color: #2D43B8; }
.example-card.demo .evidence {
    border-left: 2px solid #C7D5F8;
    color: #6B7AAA;
}
    .example-tag {
        position: absolute;
        top: 0.85rem;
        right: 0.85rem;
        background: #F0EBE3;
        border: 1px solid #E0DAD0;
        border-radius: 999px;
        padding: 0.18rem 0.6rem;
        font-size: 0.62rem;
        font-weight: 800;
        color: #9A9484;
        letter-spacing: 0.06em;
    }

    .example-card.demo .example-tag {
        background: #F97316;
        color: #FFFFFF;
        border: 1px solid #F97316;
    }

    .top-opportunity {
        font-size: 0.68rem;
        font-weight: 800;
        color: #C2410C;
        letter-spacing: 0.06em;
        margin: 0 0 0.35rem 0;
    }

    .example-title {
        margin: 0 0 0.5rem 0;
        color: #1A1A2E;
        font-size: 1.15rem;
        line-height: 1.3;
        font-weight: 800;
    }

    .example-desc {
        margin: 0 0 0.85rem 0;
        color: #4A4A6A;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .metric-row {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        margin-bottom: 0.85rem;
    }

    .solution-box {
        background: #FFF7ED;
        border-left: 3px solid #F97316;
        border-radius: 0 10px 10px 0;
        padding: 0.85rem 1rem;
        margin-bottom: 0.85rem;
    }

    .solution-label {
        margin: 0 0 0.2rem 0;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 800;
        color: #C2410C;
    }

    .solution-text {
        margin: 0;
        color: #1A1A2E;
        font-weight: 650;
        font-size: 0.9rem;
        line-height: 1.5;
    }

    .evidence {
        margin: 0;
        font-size: 0.82rem;
        color: #7A7A9A;
        font-style: italic;
        line-height: 1.55;
        padding-left: 0.75rem;
        border-left: 2px solid #E8E4DC;
    }

    .cap-banner {
        background: #FEF9C3;
        border: 1.5px solid #FEF08A;
        border-radius: 10px;
        padding: 0.65rem 1rem;
        font-size: 0.85rem;
        color: #854D0E;
        margin-bottom: 1rem;
        text-align: center;
    }

    .subtle-footer {
        text-align: center;
        font-size: 0.75rem;
        color: #C4BDB5;
        margin-top: 3rem;
        padding: 1rem 0 2rem 0;
        border-top: 1px solid #F0EBE3;
        line-height: 1.7;
    }

    /* Search form cleanup: remove Streamlit's extra wrapper styling */
    [data-testid="stForm"] {
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    .stTextInput {
        margin-bottom: 0 !important;
    }

    .stTextInput > div {
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div {
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1.5px solid #E8E4DC !important;
        padding: 0 1rem !important;
        font-size: 0.95rem !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03) !important;
        height: 48px !important;
        min-height: 48px !important;
        box-sizing: border-box !important;
        margin: 0 !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #F97316 !important;
        box-shadow: 0 0 0 3px rgba(249,115,22,0.1) !important;
        outline: none !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #B8B0A4 !important;
    }

    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #F97316, #EA580C) !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0 1.2rem !important;
        font-size: 0.92rem !important;
        height: 48px !important;
        min-height: 48px !important;
        box-shadow: 0 4px 12px rgba(249,115,22,0.2) !important;
        transition: all 0.15s ease !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(249,115,22,0.28) !important;
    }

    .stButton > button[kind="secondary"] {
        background: #17172F !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.6rem 0.75rem !important;
        font-size: 0.85rem !important;
        line-height: 1.3 !important;
        white-space: nowrap !important;
        min-height: 44px !important;
        transition: all 0.12s ease !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background: #2A2A48 !important;
        transform: translateY(-1px) !important;
    }

    .stDownloadButton > button {
        background: #FFFFFF !important;
        color: #4A4A6A !important;
        border: 1.5px solid #E8E4DC !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1rem !important;
        font-size: 0.88rem !important;
    }

    .stDownloadButton > button:hover {
        border-color: #F97316 !important;
        color: #F97316 !important;
    }

    .results-table-wrap {
        border: 1.5px solid #F0EBE3;
        border-radius: 12px;
        overflow: hidden;
        background: #FFFFFF;
        margin-bottom: 1rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.03);
    }

    .results-table {
        width: 100%;
        border-collapse: collapse;
    }

    .results-table thead tr {
        background: #FAFAF7;
        border-bottom: 2px solid #F0EBE3;
    }

    .results-table th {
        padding: 0.6rem 0.85rem;
        font-size: 0.68rem;
        color: #B8B0A4;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-weight: 800;
        text-align: left;
    }

    .results-table th.center,
    .results-table td.center {
        text-align: center;
    }

    .results-table td {
        padding: 0.65rem 0.85rem;
        border-bottom: 1px solid #F5F0E8;
        vertical-align: middle;
        font-size: 0.85rem;
    }

    .pain-card {
        background: #FFFFFF;
        border: 1.5px solid #F0EBE3;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.03);
    }

    .pain-card.top-pick {
        background: #FFFEF9;
        border: 2px solid #F97316;
    }

    .rank-label {
        margin: 0 0 0.35rem 0;
        font-size: 0.68rem;
        font-weight: 800;
        color: #C2410C;
        letter-spacing: 0.06em;
    }

    .card-title {
        margin: 0 0 0.45rem 0;
        font-size: 1.2rem;
        font-weight: 800;
        color: #1A1A2E;
        line-height: 1.3;
    }

    .card-desc {
        margin: 0 0 0.85rem 0;
        color: #4A4A6A;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        margin: 1.25rem 0 0.85rem 0;
        flex-wrap: wrap;
    }

    .results-left {
        color: #7A7A9A;
        font-weight: 700;
        font-size: 0.92rem;
        margin: 0;
    }

    .results-right {
        color: #B8B0A4;
        font-size: 0.78rem;
        margin: 0;
    }

    .empty-state-copy {
        text-align: center;
        padding: 1rem 0;
    }

    .empty-state-copy .title {
        font-weight: 800;
        color: #1A1A2E;
        font-size: 1rem;
        margin: 0 0 0.3rem 0;
    }

    .empty-state-copy .desc {
        color: #7A7A9A;
        font-size: 0.88rem;
        margin: 0;
        line-height: 1.6;
    }

    @media (max-width: 768px) {
        .results-table-wrap {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
        .results-table {
            min-width: 580px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "results":        None,
    "last_keyword":   "",
    "last_scan_time": 0.0,
    "post_count":     0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# API KEY
# Sidebar key option is commented out.
# To enable: uncomment the sidebar block below,
# change initial_sidebar_state to "auto" in set_page_config,
# and uncomment the API_KEY line that uses user_key.
# ============================================================

# -- SIDEBAR API KEY (commented out — uncomment to enable) --
# with st.sidebar:
#     st.markdown(
#         '<p style="font-weight:700;color:#1A1A2E;font-size:0.95rem;'
#         'margin-bottom:0.25rem;">Your Gemini API Key</p>',
#         unsafe_allow_html=True
#     )
#     st.caption(
#         "Optional. Use your own key if the free daily limit is reached. "
#         "Never stored — lives only in this browser session."
#     )
#     user_key = st.text_input(
#         "api_key",
#         type="password",
#         placeholder="AIza...",
#         label_visibility="collapsed"
#     )
#     if user_key.strip():
#         st.caption("Using your personal key.")
#     elif st.secrets.get("GEMINI_API_KEY", ""):
#         st.caption("Using hosted key.")
#     else:
#         st.caption("No key found.")
#     st.markdown(
#         '<p style="font-size:0.75rem;color:#B8B0A4;margin-top:0.5rem;">'
#         'Get a free key at '
#         '<a href="https://aistudio.google.com" target="_blank" '
#         'style="color:#F97316;">aistudio.google.com</a></p>',
#         unsafe_allow_html=True
#     )
#
# hosted_key = st.secrets.get("GEMINI_API_KEY", "")
# API_KEY = user_key.strip() if user_key.strip() else hosted_key  # ← uncomment with sidebar

API_KEY = st.secrets.get("GEMINI_API_KEY", "")  # ← comment out when enabling sidebar

# ============================================================
# CONFIG
# ============================================================
COOLDOWN_SECONDS = 30

EXAMPLE_QUERIES = [
    ("Sourdough",    "sourdough baking"),
    ("Marathon",     "marathon training"),
    ("Remote work",  "remote work"),
    ("Language",     "language learning"),
    ("Sleep",        "sleep tracking"),
    ("Finance",      "personal finance"),
]

# ============================================================
# HELPERS
# ============================================================
def safe(text):
    return html.escape(str(text)) if text is not None else ""

def pill_bucket(score, invert=False):
    if invert:
        if score >= 8:
            return ("#FEE2E2", "#991B1B", "#FECACA")
        if score >= 5:
            return ("#FEF9C3", "#854D0E", "#FDE68A")
        return ("#DCFCE7", "#166534", "#BBF7D0")
    if score >= 8:
        return ("#DCFCE7", "#166534", "#BBF7D0")
    if score >= 5:
        return ("#FEF9C3", "#854D0E", "#FDE68A")
    return ("#FEE2E2", "#991B1B", "#FECACA")

def score_pill_html(label, score, invert=False):
    bg, fg, border = pill_bucket(score, invert)
    text = f'{safe(score)}/10' if not label else f'{safe(label)} {safe(score)}/10'
    return (
        f'<span style="background:{bg};color:{fg};border:1.5px solid {border};'
        f'border-radius:999px;padding:0.25rem 0.65rem;font-size:0.75rem;'
        f'font-weight:700;white-space:nowrap;">{text}</span>'
    )

def crop_logo_to_b64(path):
    img = Image.open(path).convert("RGBA")

    alpha = img.getchannel("A")
    alpha_bbox = alpha.getbbox()
    if alpha_bbox:
        img = img.crop(alpha_bbox)

    rgb = img.convert("RGB")
    bg_color = rgb.getpixel((0, 0))
    bg = Image.new("RGB", rgb.size, bg_color)
    diff = ImageChops.difference(rgb, bg)
    diff = ImageChops.add(diff, diff, 2.0, -18)
    bbox = diff.getbbox()
    if bbox:
        img = img.crop(bbox)

    target_h = 88
    scale = target_h / max(img.height, 1)
    new_size = (max(1, int(img.width * scale)), target_h)
    img = img.resize(new_size, Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def render_logo():
    if os.path.exists(LOGO_PATH):
        try:
            logo_b64 = crop_logo_to_b64(LOGO_PATH)
            st.markdown(
                f'<div class="logo-row">'
                f'<img src="data:image/png;base64,{logo_b64}" alt="Curiosity Radar">'
                f'</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown(
                '<div class="logo-row" style="font-size:1.3rem;font-weight:800;'
                'color:#17172F;">📡 Curiosity Radar</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="logo-row" style="font-size:1.3rem;font-weight:800;'
            'color:#17172F;">📡 Curiosity Radar</div>',
            unsafe_allow_html=True,
        )

def render_daily_cap():
    remaining = daily_scans_remaining()
    if is_daily_cap_reached():
        st.markdown(
            '<div class="cap-banner">Daily scan limit reached — this free tool '
            'has limited capacity. Check back tomorrow.</div>',
            unsafe_allow_html=True,
        )
    elif remaining <= 30:
        st.markdown(
            f'<div class="cap-banner">{remaining} free scans remaining today.</div>',
            unsafe_allow_html=True,
        )

def render_example_card(after_results=False):
    heading = "Example result"
    subheading = "This is a demo so users can see what Curiosity Radar returns."

    if after_results:
        heading = "Demo result"
        subheading = "A sample result for comparison — your real results are shown above."

    st.markdown(
        f'<p class="mini-heading">{heading}</p>'
        f'<p class="mini-subheading">{subheading}</p>',
        unsafe_allow_html=True,
    )

    st.markdown(f"""
    <div class="example-card demo">
        <div class="example-tag">DEMO</div>
        <p class="top-opportunity">TOP OPPORTUNITY</p>
        <h3 class="example-title">No structured beginner learning path</h3>
        <p class="example-desc">
            New bakers feel overwhelmed by conflicting advice across forums,
            YouTube, and blogs — with no single guided progression from first
            loaf to advanced techniques.
        </p>
        <div class="metric-row">
            {score_pill_html("Demand", 9)}
            {score_pill_html("Difficulty", 3, invert=True)}
            {score_pill_html("Opportunity", 9)}
        </div>
        <div class="solution-box">
            <p class="solution-label">The Missing Tool</p>
            <p class="solution-text">
                A structured sourdough curriculum app — step-by-step from first
                loaf to open crumb scoring, with progress tracking at each stage.
            </p>
        </div>
        <p class="evidence">
            "I've watched 50 YouTube videos and I still feel like I have no idea
            what I'm doing. Is there any resource that walks you through this systematically?"
        </p>
    </div>
    """, unsafe_allow_html=True)

def run_scan(keyword):
    elapsed = time.time() - st.session_state.last_scan_time
    if elapsed < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - elapsed)
        st.warning(f"Please wait {remaining}s before scanning again.")
        return

    status = st.empty()
    status.info(f'Scanning Reddit for "{keyword}"…')
    posts = fetch_reddit_posts(keyword)

    if not posts:
        status.empty()
        st.session_state.results = []
        st.session_state.last_keyword = keyword
        st.session_state.post_count = 0
        st.rerun()
        return

    status.info(f"Analysing {len(posts)} posts with Gemini…")
    results = analyse_pain_points(keyword, posts, API_KEY)
    status.empty()

    if results is None:
        st.error("Analysis failed. Please try again.")
        return

    st.session_state.results = sorted(
        results,
        key=lambda x: x.get("opportunity_score", 0),
        reverse=True
    )
    st.session_state.last_keyword = keyword
    st.session_state.last_scan_time = time.time()
    st.session_state.post_count = len(posts)
    st.rerun()

def maybe_handle_scan(keyword):
    keyword = (keyword or "").strip()

    if is_daily_cap_reached():
        st.error(
            "Daily scan limit reached — this free tool runs on a limited quota. "
            "Check back tomorrow."
        )
        return

    if not keyword:
        st.error("Please enter a topic first.")
        return

    if not API_KEY:
        st.markdown("""
<div id="api-toast" style="
    position:fixed; top:1rem; right:1rem; z-index:9999;
    background:#FEF9C3; border:1.5px solid #FEF08A;
    border-radius:12px; padding:0.75rem 1rem; max-width:300px;
    box-shadow:0 4px 16px rgba(0,0,0,0.1);
    display:flex; align-items:flex-start; gap:0.75rem;
    font-size:0.82rem; color:#854D0E;
    font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
    <span style="flex:1;line-height:1.5;">
        <strong>Dev mode</strong> — No API key found.<br>
        Add <code>GEMINI_API_KEY</code> to Streamlit secrets.
    </span>
    <button onclick="document.getElementById('api-toast').style.display='none'"
        style="background:none;border:none;cursor:pointer;color:#854D0E;
               font-size:1rem;line-height:1;padding:0;flex-shrink:0;opacity:0.6;">
        ✕
    </button>
</div>
""", unsafe_allow_html=True)
        return

    run_scan(keyword)

# ============================================================
# PAGE TOP
# ============================================================
render_logo()
render_daily_cap()

has_searched = st.session_state.results is not None
has_results = bool(st.session_state.results)
scan_request = None

# ============================================================
# SEARCH UI
# ============================================================
if has_searched:
    with st.form("top_search_form", clear_on_submit=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            keyword_input = st.text_input(
                "keyword",
                placeholder="Try another topic…",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("Scan Reddit", use_container_width=True)
    if submitted:
        scan_request = keyword_input
    st.markdown('<hr class="section-divider" style="margin:1rem 0 1.25rem 0;">', unsafe_allow_html=True)

else:
    st.markdown("""
    <div class="hero-wrap">
        <h1 class="hero-title">Find what people actually want built</h1>
        <p class="hero-subtitle">
            Enter any topic. Curiosity Radar scans Reddit for real frustrations
            and turns them into ranked, buildable app ideas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("hero_search_form", clear_on_submit=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            keyword_input = st.text_input(
                "keyword",
                placeholder="e.g. plant care, marathon training, language learning…",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("Scan Reddit", use_container_width=True)
    if submitted:
        scan_request = keyword_input

    st.markdown('<p class="section-kicker">— or start with an example —</p>', unsafe_allow_html=True)

    row1 = st.columns(3, gap="small")
    for col, (label, query) in zip(row1, EXAMPLE_QUERIES[:3]):
        with col:
            if st.button(label, key=f"ex_{query}", type="secondary", use_container_width=True):
                scan_request = query

    row2 = st.columns(3, gap="small")
    for col, (label, query) in zip(row2, EXAMPLE_QUERIES[3:]):
        with col:
            if st.button(label, key=f"ex2_{query}", type="secondary", use_container_width=True):
                scan_request = query

    st.markdown('<hr class="section-divider" style="margin:2rem 0 1.5rem 0;">', unsafe_allow_html=True)

    st.markdown("""
    <div class="steps-row">
        <div class="step-item">
            <div class="step-num">1</div>
            <p class="step-label">Enter a topic</p>
            <p class="step-desc">A hobby, niche, or industry.</p>
        </div>
        <div class="step-item">
            <div class="step-num">2</div>
            <p class="step-label">Reddit is scanned</p>
            <p class="step-desc">40 posts from the past year.</p>
        </div>
        <div class="step-item">
            <div class="step-num">3</div>
            <p class="step-label">AI ranks the gaps</p>
            <p class="step-desc">Pain points scored by opportunity.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider" style="margin:0 0 1.5rem 0;">', unsafe_allow_html=True)
    render_example_card(after_results=False)

# ============================================================
# EXECUTE SCAN
# ============================================================
if scan_request is not None:
    maybe_handle_scan(scan_request)

# ============================================================
# EMPTY STATE
# ============================================================
if st.session_state.results is not None and len(st.session_state.results) == 0:
    if os.path.exists(EMPTY_STATE_PATH):
        _, img_col, _ = st.columns([1, 1.6, 1])
        with img_col:
            st.image(EMPTY_STATE_PATH, use_container_width=True)

    st.markdown("""
    <div class="empty-state-copy">
        <p class="title">No clear pain points found</p>
        <p class="desc">
            Try something more specific — like <em>sourdough starter problems</em>
            instead of <em>sourdough</em>.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# RESULTS
# ============================================================
if st.session_state.results:
    results = st.session_state.results
    kw = st.session_state.last_keyword
    post_count = st.session_state.post_count

    st.markdown(
        f'<div class="results-header">'
        f'<p class="results-left">Top opportunities for '
        f'<strong style="color:#1A1A2E;">{safe(kw)}</strong></p>'
        f'<p class="results-right">{safe(post_count)} posts analysed · AI-estimated scores</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    rows_html = ""
    for i, item in enumerate(results):
        is_top = i == 0
        row_bg = "#FFFBF5" if is_top else "#FFFFFF"
        rank_color = "#F97316" if is_top else "#B8B0A4"
        border_left = "3px solid #F97316" if is_top else "3px solid transparent"

        rows_html += (
            f'<tr style="background:{row_bg};border-left:{border_left};">'
            f'<td style="font-weight:800;color:{rank_color};">#{i+1}</td>'
            f'<td style="font-weight:{"800" if is_top else "500"};color:#1A1A2E;">'
            f'{safe(item.get("pain_point", ""))}</td>'
            f'<td class="center">{score_pill_html("", item.get("demand_score", 0))}</td>'
            f'<td class="center">{score_pill_html("", item.get("difficulty_score", 0), True)}</td>'
            f'<td class="center">{score_pill_html("", item.get("opportunity_score", 0))}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<div class="results-table-wrap">'
        f'<table class="results-table">'
        f'<thead><tr>'
        f'<th>Rank</th><th>Pain Point</th>'
        f'<th class="center">Demand</th>'
        f'<th class="center">Difficulty</th>'
        f'<th class="center">Opportunity</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(results)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download results as CSV",
        data=csv,
        file_name=f"curiosity_radar_{kw.replace(' ', '_')}.csv",
        mime="text/csv",
    )

    st.markdown('<hr class="section-divider" style="margin:1.5rem 0;">', unsafe_allow_html=True)

    for i, item in enumerate(results):
        is_top = i == 0
        badge = "TOP OPPORTUNITY" if is_top else f"#{i+1}"
        card_class = "pain-card top-pick" if is_top else "pain-card"

        metrics = (
            score_pill_html("Demand", item.get("demand_score", 0)) + " " +
            score_pill_html("Difficulty", item.get("difficulty_score", 0), invert=True) + " " +
            score_pill_html("Score", item.get("opportunity_score", 0))
        )

        st.markdown(
            f'<div class="{card_class}">'
            f'<p class="rank-label">{safe(badge)}</p>'
            f'<h3 class="card-title">{safe(item.get("pain_point", ""))}</h3>'
            f'<p class="card-desc">{safe(item.get("description", ""))}</p>'
            f'<div class="metric-row">{metrics}</div>'
            f'<div class="solution-box">'
            f'<p class="solution-label">The Missing Tool</p>'
            f'<p class="solution-text">{safe(item.get("app_idea", ""))}</p>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        with st.expander("View Reddit evidence"):
            st.markdown(
                f'<p class="evidence">"{safe(item.get("evidence", ""))}"</p>',
                unsafe_allow_html=True,
            )

    st.markdown('<hr class="section-divider" style="margin:1.75rem 0 1.25rem 0;">', unsafe_allow_html=True)
    render_example_card(after_results=True)

    st.markdown("<div style='height:0.35rem'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if st.button("New search", type="secondary", use_container_width=True):
            st.session_state.results = None
            st.session_state.last_keyword = ""
            st.session_state.post_count = 0
            st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="subtle-footer">
    Curiosity Radar · Built by BlurryRainbow · Powered by Gemini AI<br>
    Scores are AI estimates based on Reddit post analysis. Not statistically validated.
</div>
""", unsafe_allow_html=True)
