"""
comparator.py
Compares PDF prices vs local DB (fuzzy + script normalization).
If not in DB → web search returning multiple sources + average price.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from rapidfuzz import process, fuzz
from web_search import search_product_price

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).parent / "db.json"
FUZZY_THRESHOLD = 55

CYR_TO_LAT = {
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"yo","ж":"j","з":"z","и":"i",
    "й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t",
    "у":"u","ф":"f","х":"x","ц":"ts","ч":"ch","ш":"sh","щ":"sh","ъ":"'","ы":"i","ь":"",
    "э":"e","ю":"yu","я":"ya","ғ":"g'","қ":"q","ҳ":"h","ў":"o'","ҷ":"j",
    "А":"a","Б":"b","В":"v","Г":"g","Д":"d","Е":"e","Ё":"yo","Ж":"j","З":"z","И":"i",
    "Й":"y","К":"k","Л":"l","М":"m","Н":"n","О":"o","П":"p","Р":"r","С":"s","Т":"t",
    "У":"u","Ф":"f","Х":"x","Ц":"ts","Ч":"ch","Ш":"sh","Щ":"sh","Ъ":"'","Ы":"i","Ь":"",
    "Э":"e","Ю":"yu","Я":"ya","Ғ":"g'","Қ":"q","Ҳ":"h","Ў":"o'","Ҷ":"j",
}

def cyr_to_lat(t): return "".join(CYR_TO_LAT.get(c, c) for c in t)
def is_cyrillic(t): return sum(1 for c in t if "\u0400"<=c<="\u04ff") > len(t)*0.3
def normalize(t):
    if is_cyrillic(t): t = cyr_to_lat(t)
    return t.lower().strip()

def load_database():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_norm_db(db):
    return {normalize(k): (k, v) for k, v in db.items()}

def find_db_match(name, norm_db) -> Optional[tuple]:
    r = process.extractOne(normalize(name), norm_db.keys(),
                           scorer=fuzz.token_set_ratio, score_cutoff=FUZZY_THRESHOLD)
    if not r: return None
    key, score, _ = r
    orig, price = norm_db[key]
    logger.info(f"DB match: '{name}' → '{orig}' score={score:.1f}")
    return orig, price, score

def calc(pdf_price, ref_price, match_type="exact"):
    if pdf_price is None or ref_price is None:
        return None, None, "Unknown"
    diff = pdf_price - ref_price
    pct  = round((diff / pdf_price) * 100, 2)
    if match_type == "approximate":
        status = "Approx. OK" if abs(pct) < 1 else "Approx. Mismatch"
    else:
        status = "OK" if abs(pct) < 1 else "Mismatch"
    return diff, pct, status


def compare_products(products: list) -> list:
    db      = load_database()
    norm_db = build_norm_db(db)
    results = []

    for product in products:
        name      = product.get("name", "Unknown")
        pdf_price = product.get("price")

        # ── Local DB ──────────────────────────────────────────────────────
        match = find_db_match(name, norm_db)
        if match:
            orig, db_price, score = match
            diff, pct, status = calc(pdf_price, db_price, "exact")
            results.append({
                "name":            name,
                "unit":            product.get("unit"),
                "quantity":        product.get("quantity"),
                "pdf_price":       pdf_price,
                "ref_price":       db_price,
                "ref_label":       orig,
                "match_score":     round(score, 1),
                "difference":      diff,
                "percent":         pct,
                "total_with_tax":  product.get("total_with_tax"),
                "price_source":    "local_db",
                "status":          status,
                "web_prices":      None,
            })
            continue

        # ── Web search fallback ───────────────────────────────────────────
        logger.info(f"'{name}' not in DB — web search...")
        web = search_product_price(name, unit=product.get("unit", ""))

        avg_price  = web.get("average_price")
        match_type = web.get("match_type", "approximate")
        diff, pct, status = calc(pdf_price, avg_price, match_type)

        results.append({
            "name":           name,
            "unit":           product.get("unit"),
            "quantity":       product.get("quantity"),
            "pdf_price":      pdf_price,
            "ref_price":      avg_price,
            "ref_label":      f"Web avg ({match_type})",
            "match_score":    None,
            "difference":     diff,
            "percent":        pct,
            "total_with_tax": product.get("total_with_tax"),
            "price_source":   "web_search",
            "status":         status,
            "web_prices": {
                "average":  avg_price,
                "sources":  web.get("prices", []),
                "summary":  web.get("search_summary", ""),
                "match_type": match_type,
            },
        })

    return results