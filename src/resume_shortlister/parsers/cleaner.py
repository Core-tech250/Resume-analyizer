import re
from typing import Optional

def clean_text(text: Optional[str]) -> str:
    """
    Cleans and normalizes resume text:
    - Removes non-printable characters and control codes
    - Normalizes multiple spaces and tabs to single space
    - Normalizes excessive newlines
    - Strips leading and trailing whitespace
    """
    if not text:
        return ""
    
    # Remove null bytes and non-printable control characters except \n and \t
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)
    
    # Replace non-breaking spaces with standard space
    cleaned = cleaned.replace('\xa0', ' ').replace('\u200b', '')
    
    # Normalize excessive spaces and tabs on the same line
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    # Normalize multiple blank lines (max 2 consecutive newlines)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Strip whitespace line-by-line
    lines = [line.strip() for line in cleaned.splitlines()]
    cleaned = "\n".join(lines).strip()
    
    return cleaned

def generate_preview_snippet(text: str, max_chars: int = 250) -> str:
    """
    Generates a concise preview snippet from resume text.
    """
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip() + "..."
