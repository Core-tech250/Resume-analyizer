import io
import logging
from typing import Tuple
import pdfplumber
import pypdf

logger = logging.getLogger(__name__)

def parse_pdf(file_bytes: bytes) -> Tuple[str, int]:
    """
    Extracts text and page count from PDF bytes.
    First tries pdfplumber (better layout and table preservation),
    and falls back to pypdf if needed.
    """
    text = ""
    page_count = 0

    # 1. Primary: pdfplumber
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            extracted_pages = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
            text = "\n\n".join(extracted_pages).strip()
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}. Trying pypdf fallback.")

    # 2. Secondary fallback: pypdf if pdfplumber returned empty
    if not text.strip():
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)
            extracted_pages = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    extracted_pages.append(extracted)
            text = "\n\n".join(extracted_pages).strip()
        except Exception as e:
            logger.error(f"pypdf extraction failed: {e}")

    return text, page_count
