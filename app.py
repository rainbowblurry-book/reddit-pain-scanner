import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
import time
import re
import pandas as pd
from google import genai
from google.genai import types

# ============================================================
# 1. PAGE CONFIG & CSS
# ============================================================
st.set_page_config(
    page_title="Reddit Pain Radar",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stApp { background-color: #FAFAFB; }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #111827;
        -webkit-font-smoothing: antialiased;
    }

    /* Widen center column */
    [data-testid="block-container"] {
        max-width: 950px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    [data-testid="stVerticalBlock"] {
        max-width: 100% !important;
    }

    /* Input */
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        padding: 0.85rem 1.25rem !important;
        font-size: 1.1rem !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #000000 !important;
        box-shadow: 0 0 0 1px #000000 !important;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #111827 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.85rem !important;
        font-size: 1.05rem !important;
        transition: transform 0.1s ease, background-color 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #374151 !important;
        transform: translateY(-1px);
    }

    /* Secondary button */
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #374151 !important;
        border-radius: 8px !important;
        border: 1px solid #E5E7EB !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #111827 !important;
        color: #111827 !important;
    }

    /* Example topic buttons */
    .stButton > button[kind="tertiary"],
    div[data-testid="stButton"] button:not([kind="primary"]):not([kind="secondary"]) {
        background-color: #F9FAFB !important;
        color: #374151 !important;
        border-radius: 999px !important;
        border: 1px solid #E5E7EB !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.75rem !important;
        transition: all 0.15s ease !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: #374151 !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        border-color: #111827 !important;
        color: #111827 !important;
    }

    /* Cards */
    .pain-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    }
    .pain-card.top-pick {
        border: 2px solid #111827;
        background-color: #FDFDFD;
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
        font-size: 1.05rem;
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
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        color: #6B7280;
        margin-bottom: 0.5rem;
    }
    .app-solution-text {
        font-size: 1.05rem;
        font-weight: 600;
        color: #111827;
        margin: 0;
        line-height: 1.5;
    }

    .evidence-quote {
        font-size: 0.95rem;
        color: #6B7280;
        font-style: italic;
        margin: 0;
        line-height: 1.5;
    }

    /* Metric pills */
    .metric-container {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
        align-items: center;
    }
    .metric-pill {
        padding: 0.4rem 1rem;
        border-radius: 999px;
        font-size: 0.875rem;
        font-weight: 600;
        background-color: #F3F4F6;
        color: #374151;
        border: 1px solid #E5E7EB;
    }
    .pill-high { background-color: #DCFCE7; color: #166534; border-color: #BBF7D0; }
    .pill-med  { background-color: #FEF9C3; color: #854D0E; border-color: #FEF08A; }
    .pill-low  { background-color: #FEE2E2; color: #991B1B; border-color: #FECACA; }

    .ai-note {
        font-size: 0.78rem;
        color: #9CA3AF;
        margin-left: auto;
        font-style: italic;
    }

    .divider {
        border: none;
        border-top: 1px solid #E5E7EB;
        margin: 2rem 0;
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
# 2. SESSION STATE
# ============================================================
defaults = {
    "results": None,
    "last_keyword": "",
    "last_scan_time": 0,
    "post_count": 0,
    "prefill_keyword": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

API_KEY = st.secrets.get("GEMINI_API_KEY", "")
COOLDOWN_SECONDS = 30

# ============================================================
# 3. CORE LOGIC
# ============================================================
def fetch_reddit_posts(keyword, limit=40):
    headers = {"User-Agent": "PainRadar/2.0 (research tool)"}
    url = f"https://www.reddit.com/search.rss?q={keyword}&type=link&sort=relevance&limit={limit}&t=year"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception:
        st.error("Failed to connect to Reddit. They may be rate-limiting — try again in a minute.")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns) or root.findall(".//item")

    seen, results = set(), []
    for entry in entries[:limit]:
        title = (entry.findtext("atom:title", default="", namespaces=ns) or
                 entry.findtext("title", default="")).strip()
        body  = (entry.findtext("atom:content", default="", namespaces=ns) or
                 entry.findtext("description", default=""))
        body  = re.sub(r"<[^>]+>", " ", body).strip()
        if title in seen or not title:
            continue
        seen.add(title)
        results.append({"title": title, "body": body[:800]})
        time.sleep(0.05)
    return results


def analyse_pain_points(keyword, posts, api_key):
    if not posts:
        return []
    client = genai.Client(api_key=api_key)
    posts_text = "\n".join([f"Title: {p['title']}\nBody: {p['body']}" for p in posts])

    prompt = f"""
You are a product researcher. Analyze these Reddit posts about "{keyword}".
Extract the top 5 genuine user pain points, frustrations, or unmet needs that represent real product opportunities.

Scoring definitions:
- demand_score: How frequently and urgently do people express this problem? (1=rare, 10=constant/urgent)
- difficulty_score: How technically hard is it to build a solution? (1=easy, 10=very hard)
- opportunity_score: Overall product opportunity weighing high demand against low-to-medium difficulty (1-10)

For evidence, only use text that closely paraphrases or directly quotes from the posts provided below.

Posts:
{posts_text}
"""

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
                            "pain_point":        {"type": "STRING", "description": "Short name (5-8 words)"},
                            "description":       {"type": "STRING", "description": "One sentence explaining the problem"},
                            "demand_score":      {"type": "INTEGER", "description": "1 to 10"},
                            "difficulty_score":  {"type": "INTEGER", "description": "1 to 10"},
                            "opportunity_score": {"type": "INTEGER", "description": "1 to 10"},
                            "app_idea":          {"type": "STRING", "description": "One sentence describing the missing tool"},
                            "evidence":          {"type": "STRING", "description": "Close paraphrase or direct quote grounded in the posts above"}
                        },
                        "required": ["pain_point", "description", "demand_score",
                                     "difficulty_score", "opportunity_score", "app_idea", "evidence"]
                    }
                }
            )
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        return []

# ============================================================
# 4. HELPERS
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
        f'border-radius:999px; font-size:0.8rem; font-weight:700;">{score}/10</span>'
    )

RANK_CLASSES = ["", "rank-2", "rank-3", "rank-4", "rank-5"]

# ============================================================
# 5. HERO
# ============================================================
st.markdown("""
<div style="text-align:center; margin-top:3rem; margin-bottom:2rem;">
    <h1 style="font-size:2.5rem; font-weight:800; letter-spacing:-0.025em;
               margin-bottom:0.5rem; color:#111827;">
        Pain Radar
    </h1>
    <p style="color:#6B7280; font-size:1.1rem; max-width:500px; margin:0 auto;">
        Discover what people actually want built by analyzing real frustrations on Reddit.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 6. SEARCH FORM
# ============================================================
if "keyword" not in st.session_state:
    st.session_state["keyword"] = ""
if "trigger_scan" not in st.session_state:
    st.session_state["trigger_scan"] = False

with st.form(key="search_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input(
            "keyword",
            key="keyword",
            placeholder="e.g. sourdough, marathon training, AWS...",
            label_visibility="collapsed"
        )
    with col2:
        scan_clicked = st.form_submit_button(
            "Scan Reddit",
            type="primary",
            use_container_width=True
        )

# ============================================================
# 7. ONBOARDING BLOCK (only before first scan)
# ============================================================
if not st.session_state.results:

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="medium")
    steps = [
        ("🔍", "Enter any topic",
         "A niche, industry, or problem space — anything people complain about online."),
        ("📡", "We scan Reddit",
         "40 relevant posts from the past year are fetched and stripped of noise."),
        ("💡", "Gemini finds the gaps",
         "Pain points ranked by real demand, build difficulty, and opportunity score."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], steps):
        with col:
            st.markdown(f"""
<div style="text-align:center; padding:1.5rem 1.25rem; background:#FFFFFF;
            border:1px solid #E5E7EB; border-radius:12px;
            box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:1.6rem; margin-bottom:0.6rem;">{icon}</div>
    <p style="font-weight:700; color:#111827; margin:0 0 0.35rem 0;
              font-size:0.95rem;">{title}</p>
    <p style="color:#6B7280; font-size:0.82rem; margin:0;
              line-height:1.5;">{desc}</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<p style="text-align:center; color:#9CA3AF; font-size:0.82rem;
          margin-top:2rem; margin-bottom:0.75rem; letter-spacing:0.02em;">
    — or try one of these —
</p>
""", unsafe_allow_html=True)

    examples = [
        "sourdough baking", "marathon training", "remote work",
        "language learning", "sleep tracking",  "personal finance",
    ]
    ex_cols = st.columns(len(examples))
    for col, ex in zip(ex_cols, examples):
        with col:
            if st.button(ex, use_container_width=True, key=f"ex_{ex}"):
                st.session_state["keyword"] = ex
                st.session_state["trigger_scan"] = True
                st.rerun()

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border:none; border-top:1px solid #E5E7EB; margin:2.5rem 0 2rem 0;'>", unsafe_allow_html=True)

    st.markdown("""
<div style="text-align:center; margin-bottom:1.5rem;">
    <p style="font-weight:700; color:#111827; font-size:1rem; margin:0 0 0.25rem 0;">
        Here's what a scan looks like
    </p>
    <p style="color:#9CA3AF; font-size:0.82rem; margin:0;">
        Real output from the query <em>"sourdough baking"</em>
    </p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="border:2px solid #111827; border-radius:12px; padding:1.75rem;
            background:#FFFFFF; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);
            position:relative; overflow:hidden;">

    <div style="position:absolute; top:1rem; right:1.25rem;
                background:#F3F4F6; border:1px solid #E5E7EB; border-radius:999px;
                padding:0.2rem 0.75rem; font-size:0.72rem; font-weight:700;
                color:#9CA3AF; letter-spacing:0.05em;">
        EXAMPLE
    </div>

    <p style="font-size:0.8rem; font-weight:700; color:#9CA3AF;
              margin-bottom:0.5rem; letter-spacing:0.05em;">✨ TOP OPPORTUNITY</p>

    <h3 style="font-size:1.4rem; font-weight:800; color:#111827;
               margin:0 0 0.6rem 0; line-height:1.3;">
        No structured beginner learning path
    </h3>

    <p style="font-size:1rem; color:#4B5563; margin-bottom:1.25rem; line-height:1.6;">
        New bakers feel overwhelmed by conflicting advice across forums, YouTube, and blogs,
        with no single guided progression from basic loaf to advanced techniques.
    </p>

    <div style="display:flex; gap:0.75rem; margin-bottom:1.25rem; flex-wrap:wrap; align-items:center;">
        <span style="background:#DCFCE7; color:#166534; border:1px solid #BBF7D0;
                     padding:0.4rem 1rem; border-radius:999px; font-size:0.875rem; font-weight:600;">
            Demand: 9/10
        </span>
        <span style="background:#DCFCE7; color:#166534; border:1px solid #BBF7D0;
                     padding:0.4rem 1rem; border-radius:999px; font-size:0.875rem; font-weight:600;">
            Difficulty: 3/10
        </span>
        <span style="background:#DCFCE7; color:#166534; border:1px solid #BBF7D0;
                     padding:0.4rem 1rem; border-radius:999px; font-size:0.875rem; font-weight:600;">
            Score: 9/10
        </span>
        <span style="font-size:0.78rem; color:#9CA3AF; margin-left:auto; font-style:italic;">
            Gemini estimate · 40 posts
        </span>
    </div>

    <div style="background:#F3F4F6; padding:1.25rem; border-radius:8px;
                margin-bottom:1.25rem; border-left:4px solid #111827;">
        <p style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.05em;
                  font-weight:700; color:#6B7280; margin:0 0 0.4rem 0;">The Missing Tool</p>
        <p style="font-size:1.05rem; font-weight:600; color:#111827; margin:0; line-height:1.5;">
            A structured sourdough curriculum app that takes beginners step-by-step from
            their first loaf to open crumb scoring, with progress tracking and
            community feedback at each stage.
        </p>
    </div>

    <p style="font-size:0.95rem; color:#6B7280; font-style:italic; margin:0; line-height:1.5;">
        "I've watched 50 YouTube videos and read 30 blog posts and I still feel like
        I have no idea what I'm doing. Is there any resource that walks you through
        this systematically?"
    </p>
</div>
""", unsafe_allow_html=True)

    # Use cases
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown("""
<p style="text-align:center; font-weight:700; color:#111827;
          font-size:1rem; margin-bottom:1.25rem;">
    Who uses this
</p>
""", unsafe_allow_html=True)

    uc1, uc2, uc3 = st.columns(3, gap="medium")
    use_cases = [
        ("🚀", "Indie hackers",
         "Validate a niche before building. Find the real pain before writing a line of code."),
        ("📊", "Product managers",
         "Run competitive research in 30 seconds. See what users actually complain about."),
        ("✍️", "Content creators",
         "Find the exact questions people are asking. Write content that solves real problems."),
    ]
    for col, (icon, title, desc) in zip([uc1, uc2, uc3], use_cases):
        with col:
            st.markdown(f"""
<div style="padding:1.25rem; background:#FFFFFF; border:1px solid #E5E7EB;
            border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:1.4rem; margin-bottom:0.5rem;">{icon}</div>
    <p style="font-weight:700; color:#111827; font-size:0.9rem;
              margin:0 0 0.35rem 0;">{title}</p>
    <p style="color:#6B7280; font-size:0.82rem; margin:0; line-height:1.5;">{desc}</p>
</div>
""", unsafe_allow_html=True)
# ============================================================
# 8. API KEY WARNING
# ============================================================
if not API_KEY:
    st.warning("⚠️ No hosted API key found. Add GEMINI_API_KEY to your Streamlit secrets.")

# ============================================================
# 9. RATE LIMIT + EXECUTION
# ============================================================
should_scan = scan_clicked or st.session_state.get("trigger_scan", False)
active_keyword = st.session_state.get("keyword", "").strip()

if should_scan and active_keyword and API_KEY:
    st.session_state["trigger_scan"] = False
    elapsed = time.time() - st.session_state.last_scan_time
    if elapsed < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - elapsed)
        st.warning(f"⏳ Please wait {remaining}s before scanning again.")
    else:
        st.session_state.results = None
        with st.spinner("Fetching Reddit posts and analyzing with Gemini…"):
            posts = fetch_reddit_posts(active_keyword)
            if posts:
                results = analyse_pain_points(active_keyword, posts, API_KEY)
                st.session_state.results        = sorted(
                    results, key=lambda x: x.get("opportunity_score", 0), reverse=True
                )
                st.session_state.last_keyword   = active_keyword
                st.session_state.last_scan_time = time.time()
                st.session_state.post_count     = len(posts)
elif should_scan:
    st.session_state["trigger_scan"] = False

# ============================================================
# 10. RESULTS
# ============================================================
if st.session_state.results:
    results    = st.session_state.results
    kw         = st.session_state.last_keyword
    post_count = st.session_state.post_count

    # --- Header row ---
    st.markdown(f"""
<div style="display:flex; justify-content:space-between; align-items:center;
            margin-top:2rem; margin-bottom:1rem;">
    <p style="color:#6B7280; font-weight:600; font-size:1.05rem; margin:0;">
        Top opportunities for '<strong style="color:#111827;">{kw}</strong>'
    </p>
    <p style="color:#9CA3AF; font-size:0.82rem; margin:0;">
        {post_count} posts · AI-estimated scores
    </p>
</div>
""", unsafe_allow_html=True)

    # --- Premium summary table ---
    summary = [
        {
            "Rank":        f"#{i+1}",
            "Pain Point":  r["pain_point"],
            "Demand":      r["demand_score"],
            "Difficulty":  r["difficulty_score"],
            "Opportunity": r["opportunity_score"],
        }
        for i, r in enumerate(results)
    ]

    rows_html = ""
    for s in summary:
        is_top   = s["Rank"] == "#1"
        row_bg   = "#FAFFF9" if is_top else "#FFFFFF"
        rank_fw  = "font-weight:800; color:#111827;" if is_top else "font-weight:500; color:#9CA3AF;"
        title_fw = "700" if is_top else "400"

        rows_html += f"""
<tr style="background:{row_bg}; border-bottom:1px solid #F3F4F6;">
    <td style="padding:0.75rem 1rem; {rank_fw} font-size:0.875rem; white-space:nowrap;">{s["Rank"]}</td>
    <td style="padding:0.75rem 1rem; font-weight:{title_fw}; color:#111827; font-size:0.9rem;">{s["Pain Point"]}</td>
    <td style="padding:0.75rem 1rem; text-align:center;">{render_score_cell(s["Demand"])}</td>
    <td style="padding:0.75rem 1rem; text-align:center;">{render_score_cell(s["Difficulty"], invert=True)}</td>
    <td style="padding:0.75rem 1rem; text-align:center;">{render_score_cell(s["Opportunity"])}</td>
</tr>"""

    st.markdown(f"""
<div style="border:1px solid #E5E7EB; border-radius:12px; overflow:hidden;
            background:#FFFFFF; margin-bottom:1.25rem;
            box-shadow:0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);">
  <table style="width:100%; border-collapse:collapse;">
    <thead>
      <tr style="background:#F9FAFB; border-bottom:2px solid #E5E7EB;">
        <th style="padding:0.65rem 1rem; text-align:left; font-size:0.72rem; color:#6B7280;
                   text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Rank</th>
        <th style="padding:0.65rem 1rem; text-align:left; font-size:0.72rem; color:#6B7280;
                   text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Pain Point</th>
        <th style="padding:0.65rem 1rem; text-align:center; font-size:0.72rem; color:#6B7280;
                   text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Demand</th>
        <th style="padding:0.65rem 1rem; text-align:center; font-size:0.72rem; color:#6B7280;
                   text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Difficulty</th>
        <th style="padding:0.65rem 1rem; text-align:center; font-size:0.72rem; color:#6B7280;
                   text-transform:uppercase; letter-spacing:0.06em; font-weight:700;">Opportunity ↓</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
</div>
""", unsafe_allow_html=True)

    # --- CSV download ---
    df  = pd.DataFrame(results)
    csv = df.to_csv(index=False)
    st.download_button(
        label="⬇ Download full results as CSV",
        data=csv,
        file_name=f"pain_radar_{kw.replace(' ', '_')}.csv",
        mime="text/csv"
    )

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # --- Pain point cards ---
    for i, item in enumerate(results):
        is_top    = i == 0
        rank_cls  = RANK_CLASSES[min(i, 4)]
        card_cls  = "pain-card top-pick" if is_top else f"pain-card {rank_cls}"
        badge     = "✨ TOP OPPORTUNITY" if is_top else f"#{i+1}"
        title_cls = f"card-title {rank_cls}".strip()

        st.markdown(f"""
<div class="{card_cls}">
<p style="font-size:0.8rem; font-weight:700; color:#9CA3AF; margin-bottom:0.5rem;
          letter-spacing:0.05em;">{badge}</p>
<h3 class="{title_cls}">{item['pain_point']}</h3>
<p class="card-desc">{item['description']}</p>
<div class="metric-container">
  <span class="metric-pill {pill_class(item['demand_score'])}">Demand: {item['demand_score']}/10</span>
  <span class="metric-pill {pill_class(item['difficulty_score'], invert=True)}">Difficulty: {item['difficulty_score']}/10</span>
  <span class="metric-pill {pill_class(item['opportunity_score'])}">Score: {item['opportunity_score']}/10</span>
  <span class="ai-note">Gemini estimate · {post_count} posts</span>
</div>
<div class="app-solution">
  <p class="app-solution-title">The Missing Tool</p>
  <p class="app-solution-text">{item['app_idea']}</p>
</div>
<p class="evidence-quote">"{item['evidence']}"</p>
</div>
""", unsafe_allow_html=True)

    # --- Bottom new search ---
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if st.button("↑ New Search", type="secondary", use_container_width=True):
            st.session_state.results = None
            st.rerun()

# ============================================================
# 11. FOOTER
# ============================================================
st.markdown("""
<div class="subtle-footer">
    Built by BlurryRainbow · Powered by Gemini<br>
    <span style="opacity:0.6;">
        Scores are AI estimates based on Reddit post analysis — not statistically validated
    </span>
</div>
""", unsafe_allow_html=True)
