import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.parser import extract_contact_info, detect_sections, parse_years_of_experience, mask_pii

def test_extract_email():
    text = "John Doe\njohn.doe@example.com\n(555) 123-4567"
    result = extract_contact_info(text)
    assert result["email"] == "john.doe@example.com"

def test_detect_sections():
    text = "SUMMARY\nExperienced engineer\nEXPERIENCE\nSenior Dev at Acme\nSKILLS\nPython, AWS"
    sections = detect_sections(text)
    assert len(sections) > 0

def test_parse_years():
    text = "5+ years of professional experience in Python and cloud development"
    years = parse_years_of_experience(text)
    assert years >= 5

def test_mask_pii():
    text = "Contact: john@example.com or call (415) 555-0123"
    masked = mask_pii(text)
    assert "john@example.com" not in masked
    assert "[EMAIL]" in masked
