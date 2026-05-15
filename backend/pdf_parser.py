"""
pdf_parser.py
Extracts raw text from PDF files using pdfplumber.
Handles Uzbek + Russian multilingual content.
"""

import pdfplumber
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract full text from a PDF given its raw bytes.
    Returns concatenated text from all pages.
    """
    import io

    text_parts = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        logger.info(f"PDF has {len(pdf.pages)} page(s)")

        for i, page in enumerate(pdf.pages):
            # Extract plain text
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
                logger.debug(f"Page {i+1}: extracted {len(page_text)} chars")

            # Also try extracting tables (for structured invoice data)
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row:
                        cleaned = [str(cell).strip() if cell else "" for cell in row]
                        text_parts.append(" | ".join(cleaned))

    full_text = "\n".join(text_parts)
    logger.info(f"Total extracted text: {len(full_text)} characters")
    return full_text