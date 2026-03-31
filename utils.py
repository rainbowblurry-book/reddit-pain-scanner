import requests
import xml.etree.ElementTree as ET
import json
import time
import re
import streamlit as st
from google import genai
from google.genai import types


def fetch_reddit_posts(keyword, limit=40):
    headers = {"User-Agent": "PainRadar/2.0 (research tool)"}
    url = (
        f"https://www.reddit.com/search.rss"
        f"?q={keyword}&type=link&sort=relevance&limit={limit}&t=year"
    )
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception:
        st.markdown("""
<div class="empty-state">
    <p style="font-size:2rem; margin-bottom:0.75rem;">📡</p>
    <p style="font-weight:700; color:#111827; font-size:1rem; margin-bottom:0.35rem;">
        Could not reach Reddit
    </p>
    <p style="color:#6B7280; font-size:0.9rem; margin:0;">
        Reddit may be rate-limiting this server.
        Wait 60 seconds and try again.
    </p>
</div>
""", unsafe_allow_html=True)
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns) or root.findall(".//item")

    seen, results = set(), []
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
    posts_text = "\n".join(
        [f"Title: {p['title']}\nBody: {p['body']}" for p in posts]
    )

    prompt = f"""
You are a product researcher. Analyze these Reddit posts about "{keyword}".
Extract the top 5 genuine user pain points, frustrations, or unmet needs
that represent real product opportunities.

Scoring definitions:
- demand_score: How frequently and urgently do people express this problem?
  (1=rare, 10=constant/urgent)
- difficulty_score: How technically hard is it to build a solution?
  (1=easy, 10=very hard)
- opportunity_score: Overall product opportunity weighing high demand
  against low-to-medium difficulty (1-10)

For evidence, only use text that closely paraphrases or directly quotes
from the posts provided below.

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
                            "pain_point":        {"type": "STRING"},
                            "description":       {"type": "STRING"},
                            "demand_score":      {"type": "INTEGER"},
                            "difficulty_score":  {"type": "INTEGER"},
                            "opportunity_score": {"type": "INTEGER"},
                            "app_idea":          {"type": "STRING"},
                            "evidence":          {"type": "STRING"},
                        },
                        "required": [
                            "pain_point", "description", "demand_score",
                            "difficulty_score", "opportunity_score",
                            "app_idea", "evidence"
                        ]
                    }
                }
            )
        )
        return json.loads(response.text)

    except Exception as e:
        error_str = str(e).lower()
        if any(x in error_str for x in ["429", "quota", "rate", "exhausted"]):
            st.error(
                "Gemini API limit reached — free tier allows 250 requests/day "
                "and 10/minute. Wait a minute and try again, or check your "
                "quota at aistudio.google.com."
            )
        else:
            st.error(f"Analysis failed: {e}")
        return []
