import io
import logging
from typing import Optional
from PIL import Image
import pytesseract
import pdfplumber
from src.resume_shortlister.config import settings

logger = logging.getLogger(__name__)

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def is_tesseract_available() -> bool:
    """Checks if Tesseract is available on the system."""
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def ocr_pdf(file_bytes: bytes, max_pages: int = 5) -> str:
    """
    Runs OCR on PDF pages by rendering them to images and applying Tesseract.
    """
    if not is_tesseract_available():
        logger.warning("Tesseract OCR is not installed or not in PATH. Skipping OCR.")
        return ""

    extracted_texts = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages_to_process = pdf.pages[:max_pages]
            for page in pages_to_process:
                # Render page to PIL image (150 DPI for reasonable speed & clarity)
                img = page.to_image(resolution=150).original
                page_text = pytesseract.image_to_string(img)
                if page_text.strip():
                    extracted_texts.append(page_text.strip())
        return "\n\n".join(extracted_texts).strip()
    except Exception as e:
        logger.error(f"OCR failed for PDF: {e}")
        return ""

def ocr_image(image_bytes: bytes) -> str:
    """
    Runs OCR on an image (PNG, JPG, TIFF).
    """
    if not is_tesseract_available():
        return ""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        logger.error(f"OCR failed for image: {e}")
        return ""
