import re
from typing import Tuple


# Patterns for common PII
PII_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[PHONE]'),
    (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', '[CARD]'),
    (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),
]


def redact_pii(text: str) -> Tuple[str, bool]:
    """
    Redact PII from text using regex patterns.
    Returns (redacted_text, pii_was_detected).
    """
    if not text:
        return text, False

    pii_detected = False
    redacted = text

    for pattern, replacement in PII_PATTERNS:
        new_text = re.sub(pattern, replacement, redacted)
        if new_text != redacted:
            pii_detected = True
            redacted = new_text

    return redacted, pii_detected