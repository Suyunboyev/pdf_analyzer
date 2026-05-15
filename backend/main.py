"""
main.py
FastAPI backend for PDF contract analysis.
Accepts PDF uploads, extracts product data via LLM, compares with local DB.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time

from pdf_parser import extract_text_from_pdf
from ai_extractor import extract_products_from_text
from comparator import compare_products

# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PDF Contract Analyzer",
    description="Extracts product data from PDF contracts and compares prices with a local database.",
    version="1.0.0",
)

# Allow Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Response Models ──────────────────────────────────────────────────────────
class AnalyzeResponse(BaseModel):
    raw_text_preview: str
    products: list[dict[str, Any]]
    comparison: list[dict[str, Any]]
    total_products: int
    mismatches: int


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "PDF Contract Analyzer is running"}


@app.post("/analyze-pdf", response_model=AnalyzeResponse, tags=["Analysis"])
async def analyze_pdf(file: UploadFile = File(...)):
    start_total = time.perf_counter()

    # timinglarni saqlash uchun
    timings = {}

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    logger.info(f"Received file: {file.filename} ({file.content_type})")

    try:
        file_bytes = await file.read()
        logger.info(f"File size: {len(file_bytes)} bytes")

        # ───── 1. PDF + AI extraction ─────
        start_pdf = time.perf_counter()

        raw_text = extract_text_from_pdf(file_bytes)
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from PDF.")

        products = extract_products_from_text(raw_text)
        if not products:
            raise HTTPException(status_code=422, detail="No products found in the document.")

        timings["pdf_ai"] = time.perf_counter() - start_pdf

        # ───── 2. Web search + compare ─────
        start_web = time.perf_counter()

        comparison = compare_products(products)

        timings["web_search"] = time.perf_counter() - start_web

        # ───── 3. Response tayyorlash ─────
        start_response = time.perf_counter()

        mismatches = sum(1 for c in comparison if c.get("status") == "Mismatch")

        response = AnalyzeResponse(
            raw_text_preview=raw_text[:1000],
            products=products,
            comparison=comparison,
            total_products=len(products),
            mismatches=mismatches,
        )

        timings["response"] = time.perf_counter() - start_response

        # ───── TOTAL ─────
        timings["total"] = time.perf_counter() - start_total

        logger.info(
            f"""
[TIMING SUMMARY]
PDF + AI extraction: {timings['pdf_ai']:.2f} sec
Web search + compare: {timings['web_search']:.2f} sec
Response preparation: {timings['response']:.4f} sec
TOTAL: {timings['total']:.2f} sec
"""
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")