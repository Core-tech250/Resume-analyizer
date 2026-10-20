from pathlib import Path
import pytest
from src.resume_shortlister.parsers.cleaner import clean_text, generate_preview_snippet
from src.resume_shortlister.parsers.extractor import extract_resume_text
from src.resume_shortlister.parsers.pdf_parser import parse_pdf
from src.resume_shortlister.parsers.docx_parser import parse_docx

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_resumes"

def test_clean_text_normalizes_whitespace():
    raw = "  John   Doe  \n\n\nSoftware\tEngineer \x00\x08 "
    cleaned = clean_text(raw)
    assert cleaned == "John Doe\n\nSoftware Engineer"

def test_generate_preview_snippet():
    long_text = "Word " * 100
    snippet = generate_preview_snippet(long_text, max_chars=50)
    assert len(snippet) <= 55
    assert snippet.endswith("...")

def test_parse_docx_file():
    docx_file = SAMPLE_DIR / "Alex_Vance_Senior_Python_Engineer.docx"
    assert docx_file.exists()
    content = docx_file.read_bytes()
    text, para_count = parse_docx(content)
    assert len(text) > 100
    assert "Alex Vance" in text
    assert "Python" in text

def test_parse_pdf_file():
    pdf_file = SAMPLE_DIR / "Alex_Vance_Senior_Python_Engineer.pdf"
    assert pdf_file.exists()
    content = pdf_file.read_bytes()
    text, page_count = parse_pdf(content)
    assert len(text) > 100
    assert "Alex Vance" in text
    assert page_count >= 1

def test_extract_resume_text_unified():
    pdf_file = SAMPLE_DIR / "Priya_Sharma_ML_Engineer.pdf"
    content = pdf_file.read_bytes()
    result = extract_resume_text(content, pdf_file.name)
    assert result.file_type == "pdf"
    assert result.word_count > 50
    assert result.char_count > 200
    assert "Priya Sharma" in result.cleaned_text
