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
    page_title="Reddit Pain Point Scanner",
    page_icon="radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# STYLING FRONT END STYLING — EDIT THIS SECTION TO CHANGE THE LOOK
# ============================================================
# Everything between the <style> tags controls how the app looks.
# Key things you can change:
#   - background: #1e1e2e        → card background colour
#   - border: 1px solid #313244  → card border colour
#   - color: #cdd6f4             → text colour
#   - border-radius: 12px        → how rounded the corners are
#   - #f38ba8                    → TOP PICK badge colour
#   - #89b4fa                    → evidence box left border colour
# When ready to restyle, change values here and re-run Cell 4 and 5.
# ============================================================
st.markdown("""
<style>
    .main { padding: 2rem 3rem; }
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        padding: 0.75rem;
    }
    .result-card {
        background: #1e1e2e;
        border: 1px solid #313244;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .score-row {
        display: flex;
        gap: 1rem;
        margin: 0.75rem 0;
    }
    .score-pill {
        background: #313244;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .top-badge {
        background: #f38ba8;
        color: #1e1e2e;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 700;
        margin-left: 0.5rem;
    }
    .evidence-box {
        background: #181825;
        border-left: 3px solid #89b4fa;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
        color: #cdd6f4;
        margin-top: 0.75rem;
        font-style: italic;
    }
    .footer {
        text-align: center;
        color: #6c7086;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #313244;
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

        # Deduplicate
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
        return "#a6e3a1"
    elif score >= 6:
        return "#f9e2af"
    else:
        return "#f38ba8"

def render_results(pain_points, keyword):
    if not pain_points:
        st.warning(
            f"No clear pain points found for '{keyword}'. "
            "Try a more specific or complaint-heavy topic like "
            "'budgeting app frustrations' or 'running injury'."
        )
        return

    sorted_points = sorted(
        pain_points,
        key=lambda x: x.get("opportunity_score", 0),
        reverse=True
    )

    st.markdown(f"### Found {len(sorted_points)} pain points for **{keyword}**")
    st.caption("Ranked by opportunity score — highest first.")
    st.divider()

    for i, item in enumerate(sorted_points):
        is_top = i == 0
        demand = item.get("demand_score", 0)
        difficulty = item.get("difficulty_score", 0)
        opportunity = item.get("opportunity_score", 0)
        pain = item.get("pain_point", "Unknown")
        description = item.get("description", "")
        app_idea = item.get("app_idea", "")
        evidence = item.get("evidence", "")

        badge = '<span class="top-badge">TOP PICK</span>' if is_top else ""

        st.markdown(f"""
<div class="result-card">
    <h4 style="margin:0 0 0.5rem 0;">#{i+1} &mdash; {pain}{badge}</h4>
    <p style="margin:0.25rem 0; color:#cdd6f4;">{description}</p>
    <div class="score-row">
        <span class="score-pill" style="color:{score_color(demand)}">
            Demand {demand}/10
        </span>
        <span class="score-pill" style="color:{score_color(10 - difficulty)}">
            Difficulty {difficulty}/10
        </span>
        <span class="score-pill" style="color:{score_color(opportunity)}">
            Opportunity {opportunity}/10
        </span>
    </div>
    <p style="margin:0.5rem 0;"><strong>App idea:</strong> {app_idea}</p>
    <div class="evidence-box">"{evidence}"</div>
</div>
""", unsafe_allow_html=True)

    # CSV export
    st.divider()
    st.markdown("#### Export results")

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
        file_name=f"pain_points_{keyword.replace(' ', '_')}.csv",
        mime="text/csv"
    )

# ============================================================
# SESSION STATE — keeps results alive across interactions
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = None
if "last_keyword" not in st.session_state:
    st.session_state.last_keyword = ""
if "history" not in st.session_state:
    st.session_state.history = []

# ============================================================
# MAIN UI
# ============================================================

st.title("Reddit Pain Point Scanner")
st.markdown(
    "Find real user frustrations on Reddit and turn them into "
    "buildable app ideas — powered by Gemini AI."
)
st.divider()

# API key input
with st.sidebar:
    st.markdown("### Settings")
    hosted_key = st.secrets.get("GEMINI_API_KEY", "")
    if hosted_key:
        api_key_input = hosted_key
        st.caption("Running on hosted API key.")
    else:
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="Paste your Gemini API key here",
            help="Get a free key at aistudio.google.com"
        )
        st.caption(
            "Your key is never stored. It lives only in this session."
        )
    st.divider()
    if st.session_state.history:
        st.markdown("### Scan history")
        for h in reversed(st.session_state.history):
            st.caption(f"- {h}")

# Main input
col1, col2 = st.columns([4, 1])
with col1:
    keyword = st.text_input(
        "Enter a niche or topic",
        placeholder="e.g. plant care, DnD, marathon training, sourdough",
        label_visibility="collapsed"
    )
with col2:
    scan_button = st.button("Scan Reddit", use_container_width=True, type="primary")

st.caption(
    "The app scans recent public Reddit posts for this topic, "
    "then uses AI to surface the strongest pain points and app opportunities."
)

# Run scan
if scan_button:
    if not api_key_input:
        st.error("Please paste your Gemini API key in the sidebar first.")
    elif not keyword.strip():
        st.error("Please enter a keyword or topic to scan.")
    else:
        with st.spinner(f"Scanning Reddit for '{keyword}'..."):
            posts = fetch_reddit_posts(keyword.strip(), limit=25)

        if posts:
            with st.spinner(f"Analysing {len(posts)} posts with Gemini..."):
                results = analyse_pain_points(
                    keyword.strip(), posts, api_key_input
                )

            st.session_state.results = results
            st.session_state.last_keyword = keyword.strip()

            if keyword.strip() not in st.session_state.history:
                st.session_state.history.append(keyword.strip())

# Show results if they exist
if st.session_state.results is not None:
    render_results(st.session_state.results, st.session_state.last_keyword)

# Footer
st.markdown(
    '<div class="footer">Reddit Pain Point Scanner &mdash; '
    'built with Streamlit + Gemini</div>',
    unsafe_allow_html=True
)
