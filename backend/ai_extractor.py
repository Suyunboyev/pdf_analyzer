"""
ai_extractor.py
Uses Google Gemini API (new google-genai SDK) to extract structured product
data from raw PDF text. Returns strict JSON with no extra explanation.
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

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. "
        "Create backend/.env with:\nGEMINI_API_KEY=your_key_here"
    )

client = genai.Client(api_key=api_key)


def build_prompt(raw_text: str) -> str:
    return (
        "You are a data extraction specialist. Extract ALL product/goods line items "
        "from the following contract or invoice text.\n\n"
        "The text may be in Uzbek, Russian, or mixed languages.\n\n"
        "Return ONLY a valid JSON array with NO explanation, NO markdown, NO code fences.\n\n"
        "Each item must follow this exact schema:\n"
        "[\n"
        "  {\n"
        '    "name": "product name in original language",\n'
        '    "unit": "unit of measurement (tonna, kg, dona, etc.)",\n'
        '    "quantity": <float>,\n'
        '    "price": <integer, price per unit WITHOUT tax>,\n'
        '    "total": <integer, total WITHOUT tax>,\n'
        '    "vat_rate": <integer, VAT percentage e.g. 12>,\n'
        '    "vat_amount": <integer, VAT amount>,\n'
        '    "total_with_tax": <integer, total WITH tax>\n'
        "  }\n"
        "]\n\n"
        "Rules:\n"
        "- Remove all spaces from numbers (e.g. '12 725 000' -> 12725000)\n"
        "- If a field is missing, use null\n"
        "- Return ONLY the JSON array, nothing else\n\n"
        "Contract/Invoice text:\n"
        + raw_text[:8000]
    )


def extract_products_from_text(raw_text: str) -> list:
    """
    Send raw PDF text to Gemini and get back structured product data.
    Returns a list of product dicts.
    """
    prompt = build_prompt(raw_text)
    logger.info("Sending text to Gemini for extraction...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    response_text = response.text.strip()
    logger.debug(f"Gemini raw response: {response_text[:500]}")

    response_text = re.sub(r"```json\s*", "", response_text)
    response_text = re.sub(r"```\s*", "", response_text)
    response_text = response_text.strip()

    products = json.loads(response_text)

    if not isinstance(products, list):
        raise ValueError("Expected a JSON array from Gemini")

    logger.info(f"Extracted {len(products)} products")
    return products