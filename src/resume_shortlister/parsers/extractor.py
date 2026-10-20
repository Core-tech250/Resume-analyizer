from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Optional

from src.resume_shortlister.parsers.cleaner import clean_text, generate_preview_snippet
from src.resume_shortlister.parsers.pdf_parser import parse_pdf
from src.resume_shortlister.parsers.docx_parser import parse_docx
from src.resume_shortlister.parsers.ocr_parser import ocr_pdf, ocr_image, is_tesseract_available

logger = logging.getLogger(__name__)

@dataclass
class ExtractedResumeData:
    raw_text: str
    cleaned_text: str
    file_type: str
    char_count: int
    word_count: int
    preview_snippet: str
    ocr_used: bool

def extract_resume_text(file_bytes: bytes, filename: str) -> ExtractedResumeData:
    """
    Extracts, normalizes, and analyzes text from an uploaded resume file.
    Supports .pdf, .docx, .txt, and image formats with OCR fallback.
    """
    ext = Path(filename).suffix.lower()
    raw_text = ""
    ocr_used = False

    if ext == ".pdf":
        raw_text, _ = parse_pdf(file_bytes)
        # If text is too sparse (< 50 chars), it is likely a scanned PDF
        if len(raw_text.strip()) < 50:
            logger.info(f"PDF {filename} yielded < 50 characters. Triggering OCR fallback.")
            ocr_text = ocr_pdf(file_bytes)
            if ocr_text:
                raw_text = ocr_text
                ocr_used = True

    elif ext in [".docx", ".doc"]:
        if ext == ".docx":
            raw_text, _ = parse_docx(file_bytes)
        else:
            # Fallback for old .doc files: try decode or treat as binary text
            try:
                raw_text = file_bytes.decode("utf-8", errors="ignore")
            except Exception:
                raw_text = ""

    elif ext in [".txt", ".md"]:
        try:
            raw_text = file_bytes.decode("utf-8", errors="replace")
        except Exception:
            raw_text = file_bytes.decode("latin-1", errors="replace")

    elif ext in [".png", ".jpg", ".jpeg", ".tiff"]:
        raw_text = ocr_image(file_bytes)
        ocr_used = True

    else:
        raise ValueError(f"Unsupported file format: '{ext}'. Supported formats: .pdf, .docx, .txt")

    if not raw_text.strip():
        raise ValueError(f"Could not extract any readable text from '{filename}'. Please ensure the file is not corrupted or password-protected.")

    cleaned = clean_text(raw_text)
    words = cleaned.split()
    word_count = len(words)
    char_count = len(cleaned)
    preview = generate_preview_snippet(cleaned)

    return ExtractedResumeData(
        raw_text=raw_text,
        cleaned_text=cleaned,
        file_type=ext.lstrip("."),
        char_count=char_count,
        word_count=word_count,
        preview_snippet=preview,
        ocr_used=ocr_used,
    )
