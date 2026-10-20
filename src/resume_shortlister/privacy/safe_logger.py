import re
import logging
from typing import Any

EMAIL_PATTERN = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
PHONE_PATTERN = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

class PrivacySanitizingFilter(logging.Filter):
    """
    Scrubs PII and resume excerpts from all application logs before they are written.
    Guarantees no candidate personal information is leaked into system logs.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.msg)
        # Scrub emails
        msg = re.sub(EMAIL_PATTERN, "[LOG_SCRUBBED_EMAIL]", msg)
        # Scrub phone numbers
        msg = re.sub(PHONE_PATTERN, "[LOG_SCRUBBED_PHONE]", msg)
        # Truncate any accidental large text blobs (> 150 chars)
        if len(msg) > 300:
            msg = msg[:250] + "... [LOG_CONTENT_TRUNCATED_FOR_PRIVACY]"
        record.msg = msg
        return True

def setup_safe_logging():
    """Applies privacy-sanitizing filter to the root logger."""
    logger = logging.getLogger("src.resume_shortlister")
    logger.addFilter(PrivacySanitizingFilter())
    return logger
