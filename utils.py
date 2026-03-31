import requests
import xml.etree.ElementTree as ET
import json
import time
import re
import os
import streamlit as st
from datetime import date
from google import genai
from google.genai import types

# ============================================================
# DAILY CAP
# Stores a request count in a local file.
# Resets automatically each new calendar day.
# Cap is set below 250 to leave buffer for retries.
# ============================================================
DAILY_CAP       = 200
COUNTER_FILE    = "/tmp/curiosity_radar_counter.json"

def _load_counter():
    today = str(date.today())
    if os.path.exists(COUNTER_FILE):
        try:
            with open(COUNTER_FILE, "r") as f:
                data = json.load(f)
            if data.get("date") == today:
                return data.get("count", 0)
        except Exception:
            pass
    return 0

def _save_counter(count):
    today = str(date.today())
    try:
        with open(COUNTER_FILE, "w") as f:
            json.dump({"date": today, "count": count}, f)
    except Exception:
        pass

def is_daily_cap_reached():
    return _load_counter() >= DAILY_CAP

def increment_counter():
    count = _load_counter()
    _save_counter(count + 1)

def daily_scans_remaining():
    return max(0, DAILY_CAP - _load_counter())


# ============================================================
# REDDIT FETCH
# ============================================================
def fetch_reddit_posts(keyword, limit=40):
    headers = {"User-Agent": "CuriosityRadar/1.0 (research tool)"}
    url = (
        f"https://www.reddit.com/search.rss"
        f"?q={keyword}&type=link&sort=relevance&limit={limit}&t=year"
    )
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)
    except Exception:
        st.error(
            "Could not reach Reddit. They may be rate-limiting — "
            "wait 60 seconds and try again."
        )
        return []

    ns      = {"atom": "http://www.w3.org/2005/Atom"}
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


# ============================================================
# GEMINI ANALYSIS
# ============================================================
def analyse_pain_points(keyword, posts, api_key):
    if not posts:
        return []

    client     = genai.Client(api_key=api_key)
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
        increment_counter()
        return json.loads(response.text)

    except Exception as e:
        error_str = str(e).lower()
        if any(x in error_str for x in ["429", "quota", "rate", "exhausted"]):
            st.error(
                "Gemini API daily limit reached. "
                "This is a free tool with limited capacity — "
                "please check back tomorrow. "
                "If you have your own Gemini API key, "
                "you can add it in the sidebar."
            )
        else:
            st.error(f"Analysis failed: {e}")
        return []
