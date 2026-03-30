import streamlit as st
import requests
import xml.etree.ElementTree as ET
import json
import time
import re
from google import genai

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Reddit Pain Radar",
    page_icon="radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# FRONT END STYLING — EDIT THIS SECTION TO CHANGE THE LOOK
# ============================================================
# Key values to tweak:
#   Background:      #0a0a0f   → main page colour
#   Card bg:         #13131f   → result card colour
#   Card border:     #2a2a3e   → card outline
#   Accent colour:   #6366f1   → indigo, used for highlights
#   High score:      #10b981   → green
#   Mid score:       #f59e0b   → amber
#   Low score:       #ef4444   → red
#   Primary text:    #f1f5f9
#   Secondary text:  #94a3b8
# ============================================================

st.markdown("""
<style>
    /* ---- Full dark background ---- */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="block-container"] {
        background-color: #0a0a0f !important;
    }

    [data-testid="stHeader"] {
        background-color: #0a0a0f !important;
        border-bottom: 1px solid #1e1e2e;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d0d18 !important;
        border-right: 1px solid #1e1e2e;
    }

    /* ---- Global text colours ---- */
    html, body, [class*="css"], p, span, label, div {
        color: #f1f5f9;
    }

    /* ---- Input field ---- */
    .stTextInput > div > div > input {
        background-color: #13131f !important;
        border: 1px solid #2a2a3e !important;
        border-radius: 10px !important;
        color: #f1f5f9 !important;
        font-size: 1.05rem !important;
        padding: 0.75rem 1rem !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
    }

    .stTextInput > div > div > input::placeholder {
        color: #4a4a6a !important;
    }

    /* ---- Primary button ---- */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        border: none !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.75rem !important;
        transition: opacity 0.2s ease !important;
    }

    .stButton > button[kind="primary"]:hover {
        opacity: 0.85 !important;
    }

    /* ---- Download button ---- */
    .stDownloadButton > button {
        background-color: #13131f !important;
        border: 1px solid #2a2a3e !important;
        border-radius: 8px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
    }

    .stDownloadButton > button:hover {
        border-color: #6366f1 !important;
        color: #f1f5f9 !important;
    }

    /* ---- Dividers ---- */
    hr {
        border-color: #1e1e2e !important;
    }

    /* ---- Spinner text ---- */
    .stSpinner > div {
        color: #94a3b8 !important;
    }

    /* ---- Result cards ---- */
    .result-card {
        background: #13131f;
        border: 1px solid #2a2a3e;
        border-radius: 14px;
        padding: 1.75rem;
        margin-bottom: 1.25rem;
        transition: border-color 0.2s ease;
    }

    .result-card:hover {
        border-color: #6366f1;
    }

    .result-card.top-card {
        border-color: #6366f1;
        background: linear-gradient(135deg, #13131f 0%, #16162a 100%);
    }

    /* ---- Score pills ---- */
    .score-row {
        display: flex;
        gap: 0.75rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }

    .score-pill {
        background: #0a0a0f;
        border: 1px solid #2a2a3e;
        border-radius: 20px;
        padding: 0.35rem 1rem;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.02em;
    }

    /* ---- TOP PICK badge ---- */
    .top-badge {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: #ffffff;
        border-radius: 20px;
        padding: 0.2rem 0.85rem;
        font-size: 0.75rem;
        font-weight: 800;
        margin-left: 0.6rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        vertical-align: middle;
    }

    /* ---- Evidence quote ---- */
    .evidence-box {
        background: #0a0a0f;
        border-left: 3px solid #6366f1;
        padding: 0.75rem 1.1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        color: #94a3b8;
        margin-top: 1rem;
        font-style: italic;
        line-height: 1.6;
    }

    /* ---- App idea line ---- */
    .app-idea {
        color: #cbd5e1 !important;
        font-size: 0.95rem;
        margin: 0.5rem 0 0 0;
        line-height: 1.5;
    }

    /* ---- Card title ---- */
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0 0 0.5rem 0;
        line-height: 1.4;
    }

    /* ---- Card description ---- */
    .card-desc {
        color: #94a3b8;
        font-size: 0.92rem;
        margin: 0;
        line-height: 1.6;
    }

    /* ---- Footer ---- */
    .footer {
        text-align: center;
        color: #2a2a3e;
        font-size: 0.8rem;
        margin-top: 4rem;
        padding-top: 1.5rem;
        border-top: 1px solid #1e1e2e;
    }

    /* ---- Sidebar text ---- */
    .stSidebar .stMarkdown p,
    .stSidebar .stCaption {
        color: #94a3b8 !important;
    }

    /* ---- Warning and error boxes ---- */
    [data-testid="stAlert"] {
        background-color: #13131f !important;
        border-radius: 10px !important;
        border: 1px solid #2a2a3e !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# REDDIT FETCH
# ============================================================

def fetch_reddit_posts(keyword, limit=25):
    headers = {
        "User-Agent": "RedditPainScanner/1.0 (personal research tool)"
    }
    url = (
        f"https://www.reddit.com/search.rss"
        f"?q={keyword}&type=link&sort=new&limit={limit}&t=month"
    )
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        st.error("Reddit took too long to respond. Please try again.")
        return []
    except requests.exceptions.HTTPError as e:
        st.error(f"Reddit returned an error: {e}. Please try again in 30 seconds.")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to Reddit. Check your internet connection.")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError:
        st.error("Reddit returned unreadable content. Please try again.")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    if not entries:
        entries = root.findall(".//item")

    if not entries:
        st.warning(f"No posts found for '{keyword}'. Try a different keyword.")
        return []

    seen_titles = set()
    results = []

    for entry in entries[:limit]:
        title = (
            entry.findtext("atom:title", default="", namespaces=ns)
            or entry.findtext("title", default="")
        ).strip()

        body = (
            entry.findtext("atom:content", default="", namespaces=ns)
            or entry.findtext("description", default="")
        )
        body = re.sub(r"<[^>]+>", " ", body).strip()
        body = re.sub(r"\s+", " ", body)
        body = re.sub(r"&quot;", '"', body)
        body = re.sub(r"&amp;", "&", body)
        body = re.sub(r"&#39;", "'", body)

        if title in seen_titles or not title:
            continue
        seen_titles.add(title)

        results.append({
            "title": title,
            "body": body[:600],
        })
        time.sleep(0.05)

    return results

# ============================================================
# GEMINI ANALYSIS
# ============================================================

def build_prompt(keyword, posts):
    posts_text = ""
    for i, post in enumerate(posts, 1):
        posts_text += f"\n--- Post {i} ---\n"
        posts_text += f"Title: {post['title']}\n"
        if post['body']:
            posts_text += f"Content: {post['body']}\n"

    return f"""
You are an expert startup researcher helping solo founders find genuine 
app opportunities hidden inside Reddit conversations.

I have collected {len(posts)} Reddit posts related to the topic: "{keyword}"

Here are the posts:
{posts_text}

Your task:
1. Read every post carefully.
2. Identify genuine pain points — real frustrations, complaints, 
   repeated problems, or "I wish there was an app that..." moments.
3. Ignore: jokes, off-topic posts, generic advice, and anything that 
   is not a real problem a software product could solve.
4. For each pain point you find, produce a structured analysis.

Return your response as a valid JSON array. Nothing before it, nothing 
after it. No markdown, no backticks, no explanation. Just the raw JSON.

Use exactly this structure for each item:

[
  {{
    "pain_point": "Short name of the problem (5-8 words)",
    "description": "One sentence explaining the problem clearly",
    "demand_score": 7,
    "difficulty_score": 4,
    "opportunity_score": 8,
    "app_idea": "One sentence describing what the app would do",
    "evidence": "A direct quote or close paraphrase from one of the posts"
  }}
]

Scoring rules (all scores are integers from 1 to 10):
- demand_score: How many people likely have this problem? 
  (1 = very niche, 10 = affects almost everyone in this space)
- difficulty_score: How hard would this app be to build?
  (1 = very simple, 10 = extremely complex)
- opportunity_score: Overall viability as a solo founder project?
  (1 = poor opportunity, 10 = strong opportunity)

Important rules:
- Only include pain points that a software app could actually solve
- If the posts contain no genuine pain points, return an empty array: []
- Return between 1 and 8 pain points maximum
- Do not invent problems not present in the posts
- opportunity_score should roughly follow: 
  (demand_score + (10 - difficulty_score)) / 2
"""

def analyse_pain_points(keyword, posts, api_key):
    if not posts:
        return []

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(keyword, posts)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        if not isinstance(parsed, list):
            st.error("Gemini returned an unexpected format. Please try again.")
            return []

        return parsed

    except json.JSONDecodeError:
        st.error("Could not parse Gemini response. Please try again.")
        return []
    except Exception as e:
        st.error(f"Gemini request failed: {e}")
        return []

# ============================================================
# RESULT DISPLAY
# ============================================================

def score_color(score):
    if score >= 8:
        return "#10b981"
    elif score >= 6:
        return "#f59e0b"
    else:
        return "#ef4444"

def render_results(pain_points, keyword):
    if not pain_points:
        st.warning(
            f"No clear pain points found for '{keyword}'. "
            "Try a more specific or complaint-heavy topic like "
            "'budgeting app' or 'running injury'."
        )
        return

    sorted_points = sorted(
        pain_points,
        key=lambda x: x.get("opportunity_score", 0),
        reverse=True
    )

    st.markdown(
        f"<p style='color:#94a3b8; font-size:0.95rem; margin-bottom:1.5rem;'>"
        f"Found <strong style='color:#f1f5f9;'>{len(sorted_points)} pain points"
        f"</strong> for <strong style='color:#6366f1;'>{keyword}</strong> — "
        f"ranked by opportunity score.</p>",
        unsafe_allow_html=True
    )

    for i, item in enumerate(sorted_points):
        is_top = i == 0
        demand = item.get("demand_score", 0)
        difficulty = item.get("difficulty_score", 0)
        opportunity = item.get("opportunity_score", 0)
        pain = item.get("pain_point", "Unknown")
        description = item.get("description", "")
        app_idea = item.get("app_idea", "")
        evidence = item.get("evidence", "")

        badge = '<span class="top-badge">Top Pick</span>' if is_top else ""
        card_class = "result-card top-card" if is_top else "result-card"

        st.markdown(f"""
<div class="{card_class}">
    <p class="card-title">#{i+1} &mdash; {pain}{badge}</p>
    <p class="card-desc">{description}</p>
    <div class="score-row">
        <span class="score-pill" style="color:{score_color(demand)};">
            Demand &nbsp;{demand}/10
        </span>
        <span class="score-pill" style="color:{score_color(10 - difficulty)};">
            Difficulty &nbsp;{difficulty}/10
        </span>
        <span class="score-pill" style="color:{score_color(opportunity)};">
            Opportunity &nbsp;{opportunity}/10
        </span>
    </div>
    <p class="app-idea"><strong style="color:#6366f1;">App idea:</strong> {app_idea}</p>
    <div class="evidence-box">"{evidence}"</div>
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown(
        "<p style='color:#94a3b8; font-size:0.9rem; "
        "margin-bottom:0.5rem;'>Export your results</p>",
        unsafe_allow_html=True
    )

    csv_lines = ["Pain Point,Description,App Idea,Demand,Difficulty,Opportunity,Evidence"]
    for item in sorted_points:
        def clean(val):
            return str(val).replace('"', '""')
        csv_lines.append(
            f'"{clean(item.get("pain_point",""))}",'
            f'"{clean(item.get("description",""))}",'
            f'"{clean(item.get("app_idea",""))}",'
            f'{item.get("demand_score","")},'
            f'{item.get("difficulty_score","")},'
            f'{item.get("opportunity_score","")},'
            f'"{clean(item.get("evidence",""))}"'
        )
    csv_string = "\n".join(csv_lines)

    st.download_button(
        label="Download as CSV",
        data=csv_string,
        file_name=f"painradar_{keyword.replace(' ', '_')}.csv",
        mime="text/csv"
    )

# ============================================================
# SESSION STATE
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = None
if "last_keyword" not in st.session_state:
    st.session_state.last_keyword = ""
if "history" not in st.session_state:
    st.session_state.history = []

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        "<p style='color:#6366f1; font-weight:700; "
        "font-size:1rem;'>Pain Radar</p>",
        unsafe_allow_html=True
    )
    hosted_key = st.secrets.get("GEMINI_API_KEY", "")
    if hosted_key:
        api_key_input = hosted_key
        st.caption("Running on hosted API key.")
    else:
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="Paste your Gemini API key",
            help="Get a free key at aistudio.google.com"
        )
        st.caption("Your key is never stored.")

    if st.session_state.history:
        st.divider()
        st.markdown(
            "<p style='color:#94a3b8; font-size:0.85rem; "
            "font-weight:600;'>Recent scans</p>",
            unsafe_allow_html=True
        )
        for h in reversed(st.session_state.history[-5:]):
            st.caption(f"- {h}")

# ============================================================
# HERO SECTION
# ============================================================

st.markdown("""
<div style="text-align:center; padding: 3rem 1rem 2rem 1rem;">
    <div style="display:inline-block; background:rgba(99,102,241,0.12);
                border:1px solid rgba(99,102,241,0.3); border-radius:20px;
                padding:0.3rem 1.1rem; margin-bottom:1.25rem;">
        <span style="color:#818cf8; font-size:0.82rem; font-weight:600;
                     letter-spacing:0.05em;">
            POWERED BY GEMINI AI
        </span>
    </div>
    <h1 style="font-size:2.8rem; font-weight:800; color:#f1f5f9;
               line-height:1.15; margin:0 0 1rem 0;">
        Find what people<br>
        <span style="color:#6366f1;">actually want built</span>
    </h1>
    <p style="color:#94a3b8; font-size:1.05rem; max-width:480px;
              margin:0 auto; line-height:1.7;">
        Scans Reddit for real complaints and wishes, then ranks them
        as buildable app opportunities — scored by demand and difficulty.
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SEARCH BAR
# ============================================================

col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input(
        "keyword",
        placeholder="e.g. plant care, DnD, marathon training, sourdough...",
        label_visibility="collapsed"
    )
with col2:
    scan_button = st.button(
        "Scan Reddit",
        use_container_width=True,
        type="primary"
    )

st.markdown(
    "<p style='color:#4a4a6a; font-size:0.82rem; margin-top:0.25rem;'>"
    "Scans the 25 most recent public posts for this topic.</p>",
    unsafe_allow_html=True
)

st.divider()

# ============================================================
# SCAN LOGIC
# ============================================================

if scan_button:
    if not api_key_input:
        st.error("Please paste your Gemini API key in the sidebar first.")
    elif not keyword.strip():
        st.error("Please enter a keyword or topic to scan.")
    else:
        with st.spinner(f"Scanning Reddit for '{keyword}'..."):
            posts = fetch_reddit_posts(keyword.strip(), limit=25)

        if posts:
            with st.spinner(
                f"Analysing {len(posts)} posts with Gemini..."
            ):
                results = analyse_pain_points(
                    keyword.strip(), posts, api_key_input
                )

            st.session_state.results = results
            st.session_state.last_keyword = keyword.strip()

            if keyword.strip() not in st.session_state.history:
                st.session_state.history.append(keyword.strip())

# ============================================================
# RESULTS
# ============================================================

if st.session_state.results is not None:
    render_results(
        st.session_state.results,
        st.session_state.last_keyword
    )

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="footer">Reddit Pain Radar &mdash; '
    'built with Streamlit + Gemini AI</div>',
    unsafe_allow_html=True
)
