import streamlit as st
import pandas as pd
from utils import fetch_reddit_posts, analyse_pain_points
import time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Pain Radar — Find what people want built",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp { background-color: #FFFEF9; }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                     Helvetica, Arial, sans-serif;
        color: #1A1A2E;
        -webkit-font-smoothing: antialiased;
    }

    [data-testid="block-container"] {
        max-width: 780px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 0 !important;
    }

    /* Input */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 1.5px solid #E8E4DC !important;
        padding: 0.9rem 1.25rem !important;
        font-size: 1.05rem !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #F97316 !important;
        box-shadow: 0 0 0 3px rgba(249,115,22,0.12) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #B8B0A4 !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #F97316, #EA580C) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 0.9rem !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 12px rgba(249,115,22,0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(249,115,22,0.4) !important;
    }

    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background-color: #1A1A2E !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.8rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #2D2D44 !important;
        transform: translateY(-1px) !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: #4A4A6A !important;
        border: 1.5px solid #E8E4DC !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        border-color: #F97316 !important;
        color: #F97316 !important;
    }

    /* Example pill buttons */
    div[data-testid="stButton"] button {
        background-color: #FFF7ED !important;
        color: #C2410C !important;
        border-radius: 999px !important;
        border: 1.5px solid #FED7AA !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        padding: 0.3rem 0.75rem !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #F97316 !important;
        color: #FFFFFF !important;
        border-color: #F97316 !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #F97316, #EA580C) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 0.9rem !important;
        font-size: 1rem !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #1A1A2E !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        padding: 0.8rem 1.5rem !important;
    }

    /* Step cards */
    .step-card {
        background: #FFFFFF;
        border: 1.5px solid #F0EBE3;
        border-radius: 14px;
        padding: 1.5rem 1.25rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* Example result card */
    .example-card {
        background: #FFFFFF;
        border: 1.5px solid #F0EBE3;
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        position: relative;
    }

    /* Pain point result cards */
    .pain-card {
        background: #FFFFFF;
        border: 1.5px solid #F0EBE3;
        border-radius: 14px;
        padding: 2rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .pain-card:hover {
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }
    .pain-card.top-pick {
        border: none;
        background: #FFFEF9;
        position: relative;
        z-index: 0;
    }
    .pain-card.top-pick::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 14px;
        padding: 2px;
        background: linear-gradient(135deg, #F97316, #8B5CF6, #F97316, #8B5CF6);
        background-size: 300% 300%;
        animation: borderSpin 4s ease infinite;
        -webkit-mask:
            linear-gradient(#fff 0 0) content-box,
            linear-gradient(#fff 0 0);
        -webkit-mask-composite: destination-out;
        mask-composite: exclude;
        z-index: -1;
    }
    @keyframes borderSpin {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .pain-card.rank-2 { opacity: 0.97; }
    .pain-card.rank-3 { opacity: 0.94; }
    .pain-card.rank-4 { opacity: 0.91; }
    .pain-card.rank-5 { opacity: 0.88; }

    .card-title {
        font-size: 1.4rem;
        font-weight: 800;
        color: #1A1A2E;
        margin: 0 0 0.6rem 0;
        line-height: 1.3;
    }
    .card-title.rank-2 { font-size: 1.25rem; }
    .card-title.rank-3 { font-size: 1.15rem; }
    .card-title.rank-4 { font-size: 1.1rem; }
    .card-title.rank-5 { font-size: 1.05rem; }

    .card-desc {
        font-size: 0.97rem;
        color: #4A4A6A;
        margin: 0 0 1.1rem 0;
        line-height: 1.65;
    }

    .app-solution {
        background: #FFF7ED;
        border-left: 4px solid #F97316;
        border-radius: 0 10px 10px 0;
        padding: 1.1rem 1.25rem;
        margin-bottom: 1.1rem;
    }
    .app-solution-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 700;
        color: #C2410C;
        margin: 0 0 0.35rem 0;
    }
    .app-solution-text {
        font-size: 0.97rem;
        font-weight: 600;
        color: #1A1A2E;
        margin: 0;
        line-height: 1.5;
    }

    .evidence-quote {
        font-size: 0.88rem;
        color: #7A7A9A;
        font-style: italic;
        margin: 0;
        line-height: 1.6;
        padding-left: 0.75rem;
        border-left: 2px solid #E8E4DC;
    }

    .metric-row {
        display: flex;
        gap: 0.6rem;
        margin-bottom: 1.1rem;
        flex-wrap: wrap;
        align-items: center;
    }
    .mpill {
        padding: 0.3rem 0.85rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1.5px solid transparent;
    }
    .mp-green { background:#DCFCE7; color:#166534; border-color:#BBF7D0; }
    .mp-yellow { background:#FEF9C3; color:#854D0E; border-color:#FEF08A; }
    .mp-red { background:#FEE2E2; color:#991B1B; border-color:#FECACA; }
    .mp-note {
        font-size: 0.73rem;
        color: #B8B0A4;
        margin-left: auto;
        font-style: italic;
    }

    .empty-state {
        background: #FFFFFF;
        border: 1.5px solid #F0EBE3;
        border-radius: 14px;
        padding: 3rem 2rem;
        text-align: center;
        margin-top: 1rem;
    }

    .results-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 1.5rem 0 1rem 0;
    }

    .subtle-footer {
        text-align: center;
        font-size: 0.78rem;
        color: #C4BDB5;
        margin-top: 4rem;
        padding-bottom: 2rem;
        line-height: 1.8;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "results":        None,
    "last_keyword":   "",
    "last_scan_time": 0,
    "post_count":     0,
    "pending_kw":     "",
    "do_scan":        False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

API_KEY          = st.secrets.get("GEMINI_API_KEY", "")
COOLDOWN_SECONDS = 30
RANK_CLASSES     = ["", "rank-2", "rank-3", "rank-4", "rank-5"]

# ============================================================
# HELPERS
# ============================================================
def mpill(score, invert=False):
    if invert:
        if score >= 8: return "mp-red"
        if score >= 5: return "mp-yellow"
        return "mp-green"
    if score >= 8: return "mp-green"
    if score >= 5: return "mp-yellow"
    return "mp-red"

def score_cell(score, invert=False):
    cls = mpill(score, invert)
    bg = {"mp-green":"#DCFCE7","mp-yellow":"#FEF9C3","mp-red":"#FEE2E2"}[cls]
    fg = {"mp-green":"#166534","mp-yellow":"#854D0E","mp-red":"#991B1B"}[cls]
    return (
        f'<span style="background:{bg};color:{fg};padding:0.2rem 0.6rem;'
        f'border-radius:999px;font-size:0.78rem;font-weight:700;">'
        f'{score}/10</span>'
    )

def run_scan(keyword):
    elapsed = time.time() - st.session_state.last_scan_time
    if elapsed < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - elapsed)
        st.warning(f"Please wait {remaining}s before scanning again.")
        return
    with st.spinner("Scanning Reddit and thinking with Gemini… (~15 seconds)"):
        posts = fetch_reddit_posts(keyword)
        if posts:
            results = analyse_pain_points(keyword, posts, API_KEY)
            if results is not None:
                st.session_state.results = sorted(
                    results,
                    key=lambda x: x.get("opportunity_score", 0),
                    reverse=True
                )
                st.session_state.last_keyword   = keyword
                st.session_state.last_scan_time = time.time()
                st.session_state.post_count     = len(posts)

# ============================================================
# SEARCH BAR — shown at top always, compact when results exist
# ============================================================
def on_enter():
    st.session_state["do_scan"] = True

has_results = bool(st.session_state.results)

if has_results:
    # Compact bar at top when showing results
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input(
            "keyword",
            value=st.session_state["pending_kw"],
            placeholder="Try another topic…",
            label_visibility="collapsed",
            on_change=on_enter
        )
        st.session_state["pending_kw"] = ""
    with col2:
        scan_clicked = st.button(
            "Scan Reddit",
            type="primary",
            use_container_width=True
        )
    st.markdown(
        '<hr style="border:none;border-top:1px solid #F0EBE3;margin:1rem 0 0 0;">',
        unsafe_allow_html=True
    )
else:
    # ============================================================
    # HERO — only shown before first scan
    # ============================================================
    st.markdown("""
<div style="text-align:center; padding:3.5rem 1rem 0.5rem 1rem;">
    <div style="display:inline-block; background:#FFF7ED; border:1.5px solid #FED7AA;
                border-radius:999px; padding:0.3rem 1rem; margin-bottom:1.5rem;">
        <span style="color:#C2410C; font-size:0.78rem; font-weight:700;
                     letter-spacing:0.05em;">FREE TOOL FOR INDIE BUILDERS</span>
    </div>
    <h1 style="font-size:3rem; font-weight:800; letter-spacing:-0.03em;
               color:#1A1A2E; line-height:1.15; margin:0 0 1rem 0;">
        Find what people<br>actually want built 🎯
    </h1>
    <p style="color:#7A7A9A; font-size:1.05rem; max-width:440px;
              margin:0 auto 2.5rem auto; line-height:1.7;">
        Type any topic. Pain Radar scans Reddit for real frustrations
        and turns them into ranked, buildable app ideas.
    </p>
</div>
""", unsafe_allow_html=True)

    # ---- How it works ----
    c1, c2, c3 = st.columns(3, gap="medium")
    steps = [
        ("🔍", "Enter any topic",
         "A hobby, niche, or industry. Anything people complain about online."),
        ("📡", "We scan Reddit",
         "40 real posts from the past year, stripped of noise and fluff."),
        ("💡", "Gemini ranks the gaps",
         "Pain points scored by demand, build difficulty, and opportunity."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], steps):
        with col:
            st.markdown(
                f'<div class="step-card">'
                f'<div style="font-size:1.75rem;margin-bottom:0.75rem;">{icon}</div>'
                f'<p style="font-weight:700;color:#1A1A2E;font-size:0.92rem;'
                f'margin:0 0 0.4rem 0;">{title}</p>'
                f'<p style="color:#7A7A9A;font-size:0.82rem;margin:0;'
                f'line-height:1.55;">{desc}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    # ---- Example result ----
    st.markdown("""
<div style="margin:2.5rem 0 0.5rem 0; text-align:center;">
    <p style="font-weight:700; color:#1A1A2E; font-size:1rem; margin:0 0 0.25rem 0;">
        Here's what a real result looks like
    </p>
    <p style="color:#B8B0A4; font-size:0.82rem; margin:0;">
        From the query <em>sourdough baking</em>
    </p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="example-card">
    <div style="position:absolute;top:1.1rem;right:1.25rem;background:#F5F0E8;
                border:1px solid #E8E4DC;border-radius:999px;padding:0.2rem 0.75rem;
                font-size:0.72rem;font-weight:700;color:#B8B0A4;letter-spacing:0.05em;">
        EXAMPLE
    </div>
    <p style="font-size:0.75rem;font-weight:700;color:#C2410C;
              letter-spacing:0.06em;margin:0 0 0.5rem 0;">✨ TOP OPPORTUNITY</p>
    <h3 style="font-size:1.35rem;font-weight:800;color:#1A1A2E;
               margin:0 0 0.6rem 0;line-height:1.3;">
        No structured beginner learning path
    </h3>
    <p style="font-size:0.95rem;color:#4A4A6A;margin:0 0 1rem 0;line-height:1.65;">
        New bakers feel overwhelmed by conflicting advice across forums, YouTube,
        and blogs — with no single guided progression from first loaf to
        advanced techniques.
    </p>
    <div style="display:flex;gap:0.6rem;margin-bottom:1rem;flex-wrap:wrap;">
        <span style="background:#DCFCE7;color:#166534;border:1.5px solid #BBF7D0;
                     padding:0.3rem 0.85rem;border-radius:999px;font-size:0.8rem;
                     font-weight:700;">Demand 9/10</span>
        <span style="background:#DCFCE7;color:#166534;border:1.5px solid #BBF7D0;
                     padding:0.3rem 0.85rem;border-radius:999px;font-size:0.8rem;
                     font-weight:700;">Difficulty 3/10</span>
        <span style="background:#DCFCE7;color:#166534;border:1.5px solid #BBF7D0;
                     padding:0.3rem 0.85rem;border-radius:999px;font-size:0.8rem;
                     font-weight:700;">Opportunity 9/10</span>
        <span style="font-size:0.73rem;color:#B8B0A4;margin-left:auto;
                     font-style:italic;align-self:center;">Gemini · 40 posts</span>
    </div>
    <div style="background:#FFF7ED;border-left:4px solid #F97316;
                border-radius:0 10px 10px 0;padding:1rem 1.25rem;margin-bottom:1rem;">
        <p style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;
                  font-weight:700;color:#C2410C;margin:0 0 0.35rem 0;">The Missing Tool</p>
        <p style="font-size:0.95rem;font-weight:600;color:#1A1A2E;margin:0;line-height:1.5;">
            A structured sourdough curriculum app — step-by-step from first loaf
            to open crumb scoring, with progress tracking at each stage.
        </p>
    </div>
    <p style="font-size:0.87rem;color:#7A7A9A;font-style:italic;margin:0;
              line-height:1.6;padding-left:0.75rem;border-left:2px solid #E8E4DC;">
        "I've watched 50 YouTube videos and read 30 blog posts and I still feel
        like I have no idea what I'm doing. Is there any resource that walks
        you through this systematically?"
    </p>
</div>
""", unsafe_allow_html=True)

    # ---- Search bar ----
    st.markdown(
        '<div style="margin:2.5rem 0 0.75rem 0; text-align:center;">'
        '<p style="font-weight:700;color:#1A1A2E;font-size:1rem;margin:0 0 0.25rem 0;">'
        'Ready to find your niche? 👇</p>'
        '<p style="color:#B8B0A4;font-size:0.82rem;margin:0;">'
        'Takes about 15 seconds.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input(
            "keyword",
            value=st.session_state["pending_kw"],
            placeholder="e.g. plant care, DnD, marathon training…",
            label_visibility="collapsed",
            on_change=on_enter
        )
        st.session_state["pending_kw"] = ""
    with col2:
        scan_clicked = st.button(
            "Scan Reddit",
            type="primary",
            use_container_width=True
        )

    # ---- Example pills ----
    st.markdown(
        '<p style="text-align:center;color:#B8B0A4;font-size:0.78rem;'
        'margin:1.25rem 0 0.6rem 0;">— or try one of these —</p>',
        unsafe_allow_html=True
    )
    examples = [
        "sourdough baking", "marathon training", "remote work",
        "language learning", "sleep tracking", "personal finance",
    ]
    ex_cols = st.columns(len(examples))
    for col, ex in zip(ex_cols, examples):
        with col:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                st.session_state["pending_kw"] = ex
                st.session_state["do_scan"]    = True
                st.rerun()

# ============================================================
# SCAN EXECUTION
# ============================================================
active_keyword = keyword.strip()
should_scan    = scan_clicked or st.session_state["do_scan"]
st.session_state["do_scan"] = False

if not API_KEY:
    st.warning("No API key found. Add GEMINI_API_KEY to Streamlit secrets.")
elif should_scan and not active_keyword:
    st.error("Please enter a topic first.")
elif should_scan and active_keyword:
    run_scan(active_keyword)

# ============================================================
# RESULTS
# ============================================================
if st.session_state.results is not None and len(st.session_state.results) == 0:
    st.markdown("""
<div class="empty-state">
    <p style="font-size:2rem;margin-bottom:0.5rem;">🤔</p>
    <p style="font-weight:700;color:#1A1A2E;font-size:1rem;margin-bottom:0.35rem;">
        No clear pain points found</p>
    <p style="color:#7A7A9A;font-size:0.9rem;margin:0;">
        Try something more specific —
        like <em>sourdough starter problems</em> instead of <em>sourdough</em>.
    </p>
</div>
""", unsafe_allow_html=True)

if st.session_state.results:
    results    = st.session_state.results
    kw         = st.session_state.last_keyword
    post_count = st.session_state.post_count

    # Results header
    st.markdown(
        f'<div class="results-header">'
        f'<p style="color:#7A7A9A;font-weight:600;font-size:0.95rem;margin:0;">'
        f'Top opportunities for '
        f'<strong style="color:#1A1A2E;">{kw}</strong></p>'
        f'<p style="color:#B8B0A4;font-size:0.8rem;margin:0;">'
        f'{post_count} posts · AI-estimated</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Summary table
    rows_html = ""
    for i, r in enumerate(results):
        is_top      = i == 0
        row_bg      = "#FFFBF5" if is_top else "#FFFFFF"
        rank_style  = "font-weight:800;color:#F97316;" if is_top else "font-weight:500;color:#B8B0A4;"
        title_fw    = "700" if is_top else "400"
        border_left = "border-left:3px solid #F97316;" if is_top else "border-left:3px solid transparent;"
        rows_html += (
            f'<tr style="background:{row_bg};border-bottom:1px solid #F5F0E8;{border_left}">'
            f'<td style="padding:0.7rem 1rem;{rank_style}font-size:0.85rem;">#{i+1}</td>'
            f'<td style="padding:0.7rem 1rem;font-weight:{title_fw};color:#1A1A2E;font-size:0.88rem;">{r["pain_point"]}</td>'
            f'<td style="padding:0.7rem 1rem;text-align:center;">{score_cell(r["demand_score"])}</td>'
            f'<td style="padding:0.7rem 1rem;text-align:center;">{score_cell(r["difficulty_score"],invert=True)}</td>'
            f'<td style="padding:0.7rem 1rem;text-align:center;">{score_cell(r["opportunity_score"])}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<div style="border:1.5px solid #F0EBE3;border-radius:12px;overflow:hidden;'
        f'background:#FFFFFF;margin-bottom:1rem;'
        f'box-shadow:0 2px 8px rgba(0,0,0,0.04);">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#FAFAF7;border-bottom:2px solid #F0EBE3;">'
        f'<th style="padding:0.6rem 1rem;text-align:left;font-size:0.7rem;color:#B8B0A4;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;">Rank</th>'
        f'<th style="padding:0.6rem 1rem;text-align:left;font-size:0.7rem;color:#B8B0A4;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;">Pain Point</th>'
        f'<th style="padding:0.6rem 1rem;text-align:center;font-size:0.7rem;color:#B8B0A4;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;">Demand</th>'
        f'<th style="padding:0.6rem 1rem;text-align:center;font-size:0.7rem;color:#B8B0A4;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;">Difficulty</th>'
        f'<th style="padding:0.6rem 1rem;text-align:center;font-size:0.7rem;color:#B8B0A4;text-transform:uppercase;letter-spacing:0.07em;font-weight:700;">Opportunity</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True
    )

    df  = pd.DataFrame(results)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download results as CSV",
        data=csv,
        file_name=f"pain_radar_{kw.replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.markdown(
        '<hr style="border:none;border-top:1px solid #F0EBE3;margin:2rem 0;">',
        unsafe_allow_html=True
    )

    # Pain point cards
    for i, item in enumerate(results):
        is_top    = i == 0
        rank_cls  = RANK_CLASSES[min(i, 4)]
        card_cls  = "pain-card top-pick" if is_top else f"pain-card {rank_cls}"
        badge     = "✨ TOP OPPORTUNITY" if is_top else f"#{i+1}"
        title_cls = f"card-title {rank_cls}".strip()
        pc        = mpill(item["demand_score"])
        dc        = mpill(item["difficulty_score"], invert=True)
        oc        = mpill(item["opportunity_score"])

        st.markdown(
            f'<div class="{card_cls}">'
            f'<p style="font-size:0.72rem;font-weight:700;color:#C2410C;'
            f'letter-spacing:0.06em;margin:0 0 0.4rem 0;">{badge}</p>'
            f'<h3 class="{title_cls}">{item["pain_point"]}</h3>'
            f'<p class="card-desc">{item["description"]}</p>'
            f'<div class="metric-row">'
            f'<span class="mpill {pc}">Demand {item["demand_score"]}/10</span>'
            f'<span class="mpill {dc}">Difficulty {item["difficulty_score"]}/10</span>'
            f'<span class="mpill {oc}">Score {item["opportunity_score"]}/10</span>'
            f'<span class="mp-note">Gemini · {post_count} posts</span>'
            f'</div>'
            f'<div class="app-solution">'
            f'<p class="app-solution-label">The Missing Tool</p>'
            f'<p class="app-solution-text">{item["app_idea"]}</p>'
            f'</div>'
            f'<p class="evidence-quote">"{item["evidence"]}"</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    # New search button
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("New Search", type="secondary", use_container_width=True):
            st.session_state.results       = None
            st.session_state["pending_kw"] = ""
            st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="subtle-footer">
    🎯 Pain Radar · Built by BlurryRainbow · Powered by Gemini AI<br>
    <span style="opacity:0.7;">
        Scores are AI estimates based on Reddit post analysis.
        Not statistically validated.
    </span>
</div>
""", unsafe_allow_html=True)
