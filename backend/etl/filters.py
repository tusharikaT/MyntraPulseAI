"""
Filters and cleaning utilities for the ETL pipeline.
"""
import re
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Ensure consistent language detection
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """Detect language of the text. Returns 'en' for English, or language code, or 'unknown'."""
    if not text or len(text.strip()) < 5:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def is_relevant(text: str, keywords: list) -> bool:
    """Check if the text contains any of the relevance keywords (case-insensitive)."""
    if not text:
        return False
    
    text_lower = text.lower()
    for kw in keywords:
        # Pad keyword to match word boundaries loosely if needed, 
        # but simple substring match is fine for our broad relevance pass.
        if kw.lower() in text_lower:
            return True
    return False

def clean_text(raw_text: str) -> str:
    """
    Clean the raw text:
    1. Strip HTML tags
    2. Normalize whitespace
    3. Mask PII (emails, phone numbers)
    """
    if not raw_text:
        return ""
        
    # 1. Strip HTML
    try:
        # Using html.parser for speed and simplicity
        soup = BeautifulSoup(raw_text, "html.parser")
        text = soup.get_text(separator=" ")
    except Exception:
        text = raw_text
        
    # 2. Mask PII
    # Emails
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    text = re.sub(email_pattern, '[EMAIL]', text)
    
    # Phone numbers (basic Indian format + generic 10 digit)
    phone_pattern = r'(\+91[\-\s]?)?[6789]\d{9}'
    text = re.sub(phone_pattern, '[PHONE]', text)
    
    # 3. Normalize whitespace (remove multiple spaces, tabs, newlines)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
