import streamlit as st
import pandas as pd
from utils import fetch_reddit_posts, analyse_pain_points
import time

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Reddit Pain Radar",
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

    .stApp { background-color: #FAFAFB; }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                     Helvetica, Arial, sans-serif;
        color: #111827;
        -webkit-font-smoothing: antialiased;
    }

    [data-testid="block-container"] {
        max-width: 820px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        padding: 0.85rem 1.25rem !important;
        font-size: 1.1rem !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #000000 !important;
        box-shadow: 0 0 0 1px #000000 !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #9CA3AF !important;
    }

    .stButton > button[kind="primary"] {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.85rem !important;
        font-size: 1.05rem !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #374151 !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 2px solid #111827 !important;
        font-weight: 700 !important;
        padding: 0.75rem !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #374151 !important;
    }

    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stDownloadButton > button:hover {
        border-color: #111827 !important;
        color: #111827 !important;
    }

    .pain-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05),
                    0 2px 4px -1px rgba(0,0,0,0.03);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .pain-card:hover {
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.08);
        transform: translateY(-1px);
    }
    .pain-card.top-pick {
        background-color: #FDFDFD;
        border: none;
        position: relative;
        z-index: 0;
    }
    .pain-card.top-pick::before {
        content: "";
        position: absolute;
        inset: 0;
        border-radius: 12px;
        padding: 2px;
        background: linear-gradient(135deg, #111827, #6366f1, #111827, #6366f1);
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
        font-size: 1.5rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.75rem;
        margin-top: 0;
        line-height: 1.3;
    }
    .card-title.rank-2 { font-size: 1.35rem; }
    .card-title.rank-3 { font-size: 1.25rem; }
    .card-title.rank-4 { font-size: 1.2rem; }
    .card-title.rank-5 { font-size: 1.15rem; }

    .card-desc {
        font-size: 1rem;
        color: #4B5563;
        margin-bottom: 1.25rem;
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
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: #6B7280;
        margin-bottom: 0.4rem;
    }
    .app-solution-text {
        font-size: 1rem;
        font-weight: 600;
        color: #111827;
        margin: 0;
        line-height: 1.5;
    }

    .evidence-quote {
        font-size: 0.9rem;
        color: #6B7280;
        font-style: italic;
        margin: 0;
        line-height: 1.5;
    }

    .metric-container {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
        align-items: center;
    }
    .metric-pill {
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        border: 1px solid #E5E7EB;
    }
    .pill-high { background:#DCFCE7; color:#166534; border-color:#BBF7D0; }
    .pill-med  { background:#FEF9C3; color:#854D0E; border-color:#FEF08A; }
    .pill-low  { background:#FEE2E2; color:#991B1B; border-color:#FECACA; }

    .ai-note {
        font-size: 0.75rem;
        color: #9CA3AF;
        margin-left: auto;
        font-style: italic;
    }

    .empty-state {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
        margin-top: 1rem;
    }

    .subtle-footer {
        text-align: center;
        font-size: 0.82rem;
        color: #9CA3AF;
        margin-top: 4rem;
        padding-bottom: 2rem;
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
def pill_class(score, invert=False):
    if invert:
        return "pill-low" if score >= 8 else ("pill-med" if score >= 5 else "pill-high")
    return "pill-high" if score >= 8 else ("pill-med" if score >= 5 else "pill-low")


def render_score_cell(score, invert=False):
    cls = pill_class(score, invert=invert)
    colors = {
        "pill-high": ("#DCFCE7", "#166534"),
        "pill-med":  ("#FEF9C3", "#854D0E"),
        "pill-low":  ("#FEE2E2", "#991B1B"),
    }
    bg, fg = colors[cls]
    return (
        f'<span style="background:{bg}; color:{fg}; padding:0.2rem 0.65rem; '
        f'border-radius:999px; font-size:0.8rem; font-weight:700;">'
        f'{score}/10</span>'
    )


def run_scan(keyword):
    elapsed = time.time() - st.session_state.last_scan_time
    if elapsed < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - elapsed)
        st.warning(f"Please wait {remaining}s before scanning again.")
        return
    st.session_state.results = None
    with st.spinner("Fetching Reddit posts and analysing with Gemini…"):
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
# HERO
# ============================================================
st.markdown("""
<div style="text-align:center; margin-top:3rem; margin-bottom:2rem;">
    <h1 style="font-size:3.25rem; font-weight:800; letter-spacing:-0.03em;
               margin-bottom:0.5rem; color:#111827; line-height:1.1;">
        Pain Radar
    </h1>
    <p style="color:#6B7280; font-size:1.05rem; max-width:460px;
              margin:0 auto; line-height:1.6;">
        Discover what people actually want built — by analysing real
        frustrations on Reddit.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SEARCH BAR
# ============================================================
def on_enter():
    st.session_state["do_scan"] = True

col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input(
        "keyword",
        value=st.session_state["pending_kw"],
        placeholder="e.g. sourdough, marathon training, AWS...",
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

if not API_KEY:
    st.warning("No hosted API key found. Add GEMINI_API_KEY to Streamlit secrets.")

# ============================================================
# ONBOARDING — only shown before first scan
# ============================================================
if st.session_state.results is None:

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")
    steps = [
        ("🔍", "Enter any topic",
         "A niche, hobby, or industry — anything people complain about online."),
        ("📡", "We scan Reddit",
         "40 relevant posts from the past year, stripped of noise."),
        ("💡", "Gemini finds the gaps",
         "Pain points ranked by demand, build difficulty, and opportunity."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], steps):
        with col:
            st.markdown(
                f'<div style="text-align:center; padding:1.5rem 1rem; '
                f'background:#FFFFFF; border:1px solid #E5E7EB; '
                f'border-radius:12px;">'
                f'<div style="font-size:1.5rem; margin-bottom:0.5rem;">{icon}</div>'
                f'<p style="font-weight:700; color:#111827; margin:0 0 0.3rem 0; '
                f'font-size:0.9rem;">{title}</p>'
                f'<p style="color:#6B7280; font-size:0.8rem; margin:0; '
                f'line-height:1.5;">{desc}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown(
        '<p style="text-align:center; color:#9CA3AF; font-size:0.8rem; '
        'margin-top:2rem; margin-bottom:0.75rem;">— or try one of these —</p>',
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

if should_scan and not active_keyword:
    st.error("Please enter a topic to scan.")
elif should_scan and not API_KEY:
    st.error("No Gemini API key found. Add GEMINI_API_KEY to Streamlit secrets.")
elif should_scan and active_keyword and API_KEY:
    run_scan(active_keyword)

# ============================================================
# RESULTS
# ============================================================
if st.session_state.results is not None and len(st.session_state.results) == 0:
    st.markdown("""
<div class="empty-state">
    <p style="font-size:2rem; margin-bottom:0.5rem;">🔍</p>
    <p style="font-weight:700; color:#111827; font-size:1rem;
              margin-bottom:0.35rem;">No clear pain points found</p>
    <p style="color:#6B7280; font-size:0.9rem; margin:0;">
        Try something more specific — like
        <em>sourdough starter problems</em> instead of <em>sourdough</em>.
    </p>
</div>
""", unsafe_allow_html=True)

if st.session_state.results:
    results    = st.session_state.results
    kw         = st.session_state.last_keyword
    post_count = st.session_state.post_count

    st.markdown(
        f'<div style="display:flex; justify-content:space-between; '
        f'align-items:center; margin-top:2rem; margin-bottom:1rem;">'
        f'<p style="color:#6B7280; font-weight:600; font-size:1rem; margin:0;">'
        f'Top opportunities for '
        f'\'<strong style="color:#111827;">{kw}</strong>\''
        f'</p>'
        f'<p style="color:#9CA3AF; font-size:0.82rem; margin:0;">'
        f'{post_count} posts · AI-estimated scores</p>'
        f'</div>',
        unsafe_allow_html=True
    )

    rows_html = ""
    for i, r in enumerate(results):
        is_top      = i == 0
        row_bg      = "#FAFFF9" if is_top else "#FFFFFF"
        rank_fw     = "font-weight:800; color:#111827;" if is_top else "font-weight:500; color:#9CA3AF;"
        title_fw    = "700" if is_top else "400"
        border_left = "border-left:3px solid #111827;" if is_top else "border-left:3px solid transparent;"
        rows_html += (
            f'<tr style="background:{row_bg}; border-bottom:1px solid #F3F4F6; {border_left}">'
            f'<td style="padding:0.75rem 1rem; {rank_fw} font-size:0.875rem;">#{i+1}</td>'
            f'<td style="padding:0.75rem 1rem; font-weight:{title_fw}; color:#111827; font-size:0.88rem;">{r["pain_point"]}</td>'
            f'<td style="padding:0.75rem 1rem; text-align:center;">{render_score_cell(r["demand_score"])}</td>'
            f'<td style="padding:0.75rem 1rem; text-align:center;">{render_score_cell(r["difficulty_score"], invert=True)}</td>'
            f'<td style="padding:0.75rem 1rem; text-align:center;">{render_score_cell(r["opportunity_score"])}</td>'
            f'</tr>'
        )

    st.markdown(
        f'<div style="border:1px solid #E5E7EB; border-radius:12px; overflow:hidden; '
        f'background:#FFFFFF; margin-bottom:1.25rem; '
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
        f'<table style="width:100%; border-collapse:collapse;">'
        f'<thead><tr style="background:#F9FAFB; border-bottom:2px solid #E5E7EB;">'
        f'<th style="padding:0.65rem 1rem; text-align:left; font-size:0.72rem; color:#6B7280; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Rank</th>'
        f'<th style="padding:0.65rem 1rem; text-align:left; font-size:0.72rem; color:#6B7280; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Pain Point</th>'
        f'<th style="padding:0.65rem 1rem; text-align:center; font-size:0.72rem; color:#6B7280; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Demand</th>'
        f'<th style="padding:0.65rem 1rem; text-align:center; font-size:0.72rem; color:#6B7280; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Difficulty</th>'
        f'<th style="padding:0.65rem 1rem; text-align:center; font-size:0.72rem; color:#6B7280; text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Opportunity</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True
    )

    df  = pd.DataFrame(results)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download full results as CSV",
        data=csv,
        file_name=f"pain_radar_{kw.replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.markdown(
        '<hr style="border:none; border-top:1px solid #E5E7EB; margin:2rem 0;">',
        unsafe_allow_html=True
    )

    for i, item in enumerate(results):
        is_top    = i == 0
        rank_cls  = RANK_CLASSES[min(i, 4)]
        card_cls  = "pain-card top-pick" if is_top else f"pain-card {rank_cls}"
        badge     = "✨ TOP OPPORTUNITY" if is_top else f"#{i+1}"
        title_cls = f"card-title {rank_cls}".strip()

        st.markdown(
            f'<div class="{card_cls}">'
            f'<p style="font-size:0.75rem; font-weight:700; color:#9CA3AF; '
            f'margin-bottom:0.5rem; letter-spacing:0.05em;">{badge}</p>'
            f'<h3 class="{title_cls}">{item["pain_point"]}</h3>'
            f'<p class="card-desc">{item["description"]}</p>'
            f'<div class="metric-container">'
            f'<span class="metric-pill {pill_class(item["demand_score"])}">Demand: {item["demand_score"]}/10</span>'
            f'<span class="metric-pill {pill_class(item["difficulty_score"], invert=True)}">Difficulty: {item["difficulty_score"]}/10</span>'
            f'<span class="metric-pill {pill_class(item["opportunity_score"])}">Score: {item["opportunity_score"]}/10</span>'
            f'<span class="ai-note">Gemini · {post_count} posts</span>'
            f'</div>'
            f'<div class="app-solution">'
            f'<p class="app-solution-title">The Missing Tool</p>'
            f'<p class="app-solution-text">{item["app_idea"]}</p>'
            f'</div>'
            f'<p class="evidence-quote">"{item["evidence"]}"</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("New Search", type="secondary", use_container_width=True):
            st.session_state.results    = None
            st.session_state["pending_kw"] = ""
            st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="subtle-footer">
    Built by BlurryRainbow · Powered by Gemini<br>
    <span style="opacity:0.6;">
        Scores are AI estimates — not statistically validated
    </span>
</div>
""", unsafe_allow_html=True)
