"""
web_search.py
Searches multiple sources for product prices using Gemini Google Search grounding.
Returns individual prices per source + calculated average.
"""

import json
import logging
import os
import re

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
SEARCH_TOOL = types.Tool(google_search=types.GoogleSearch())


def _call_gemini(prompt: str, use_search: bool = True) -> str:
    cfg = types.GenerateContentConfig(tools=[SEARCH_TOOL]) if use_search else None
    r = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=cfg,
    )
    return r.text.strip()


def _parse_json(text: str):
    text = re.sub(r"```json\s*|```\s*", "", text).strip()
    m = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return None


def search_product_price(product_name: str, unit: str = "") -> dict:
    """
    Search price from multiple sources using Gemini Google Search grounding.
    Returns:
    {
        "average_price": int,
        "prices": [
            {"source": "...", "url": "...", "price": int, "note": "..."},
            ...
        ],
        "match_type": "exact" | "approximate",
        "search_summary": "...",
        "found": True
    }
    """
    unit_hint = f"({unit})" if unit else ""

    # ── Attempt 1: Multi-source structured search ─────────────────────────────
    prompt1 = f"""Using Google Search, find the current market price of this product in Uzbekistan in UZS:
Product: {product_name} {unit_hint}

Search across multiple sources: e-commerce sites, agricultural portals, government price databases, marketplaces (olx.uz, uzum.uz, agro.uz, dehqon.uz, or similar Uzbek sites).

Return ONLY this JSON array of price results (no markdown, no explanation):
{{
  "prices": [
    {{
      "source": "website or portal name",
      "url": "url if available, else null",
      "price": <integer price in UZS>,
      "note": "brief context e.g. wholesale, retail, per tonna"
    }}
  ],
  "match_type": "exact" or "approximate",
  "search_summary": "short summary of findings"
}}

Rules:
- Find AT LEAST 2-3 different sources
- If exact product not found, use the most similar product and set match_type to "approximate"
- All prices must be integers in UZS
- Never return empty prices array — always provide at least 2 estimates
"""

    try:
        raw = _call_gemini(prompt1, use_search=True)
        logger.debug(f"Attempt 1 raw: {raw[:400]}")
        result = _parse_json(raw)
        if result and result.get("prices") and len(result["prices"]) >= 1:
            prices = [p for p in result["prices"] if p.get("price")]
            if prices:
                avg = int(sum(p["price"] for p in prices) / len(prices))
                logger.info(f"'{product_name}': {len(prices)} sources, avg={avg:,} UZS")
                return {
                    "found": True,
                    "average_price": avg,
                    "prices": prices,
                    "match_type": result.get("match_type", "exact"),
                    "search_summary": result.get("search_summary", ""),
                }
    except Exception as e:
        logger.error(f"Attempt 1 failed: {e}")

    # ── Attempt 2: Pure LLM knowledge estimate ────────────────────────────────
    prompt3 = f"""Based on your knowledge of Uzbekistan's agricultural and commodity markets,
estimate the current price of "{product_name}" in UZS.
Provide 2-3 different price estimates as if from different market sources.

Return ONLY this JSON:
{{
  "prices": [
    {{"source": "Wholesale market estimate", "url": null, "price": <integer UZS>, "note": "wholesale"}},
    {{"source": "Retail market estimate",    "url": null, "price": <integer UZS>, "note": "retail"}},
    {{"source": "AI market knowledge",       "url": null, "price": <integer UZS>, "note": "average estimate"}}
  ],
  "match_type": "approximate",
  "search_summary": "AI-based price estimate from market knowledge"
}}
"""
    try:
        raw = _call_gemini(prompt3, use_search=False)
        result = _parse_json(raw)
        if result and result.get("prices"):
            prices = [p for p in result["prices"] if p.get("price")]
            if prices:
                avg = int(sum(p["price"] for p in prices) / len(prices))
                logger.info(f"Attempt 3 '{product_name}': LLM estimate avg={avg:,}")
                return {
                    "found": True,
                    "average_price": avg,
                    "prices": prices,   
                    "match_type": "approximate",
                    "search_summary": "Price estimated from AI market knowledge",
                }
    except Exception as e:
        logger.error(f"Attempt 3 failed: {e}")

    logger.error(f"All attempts failed for '{product_name}'")
    return {
        "found": False,
        "average_price": None,
        "prices": [],
        "match_type": "approximate",
        "search_summary": "Could not retrieve price.",
    }