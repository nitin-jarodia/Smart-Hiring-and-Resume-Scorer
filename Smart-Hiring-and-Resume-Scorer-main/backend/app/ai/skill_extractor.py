import re
from typing import List, Set, Tuple
from .skills_data import SKILL_LOOKUP, SKILL_SYNONYMS, normalize_skill

def extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text using the skill dictionary."""
    text_lower = text.lower()
    found_skills: Set[str] = set()
    
    # Sort by length descending to match longer phrases first
    all_patterns = sorted(SKILL_LOOKUP.keys(), key=len, reverse=True)
    
    for pattern in all_patterns:
        # Word boundary matching
        escaped = re.escape(pattern)
        if re.search(r'\b' + escaped + r'\b', text_lower):
            canonical = SKILL_LOOKUP[pattern]
            found_skills.add(canonical)
    
    return sorted(list(found_skills))

def compare_skills(jd_skills: List[str], resume_skills: List[str]) -> Tuple[List[str], List[str], float]:
    """
    Compare JD skills with resume skills.
    Returns: (matched, missing, match_ratio)
    """
    jd_canonical = set(normalize_skill(s) for s in jd_skills)
    resume_canonical = set(normalize_skill(s) for s in resume_skills)
    
    matched = list(jd_canonical & resume_canonical)
    missing = list(jd_canonical - resume_canonical)
    
    match_ratio = len(matched) / len(jd_canonical) if jd_canonical else 0.0
    
    return matched, missing, match_ratio

def extract_required_skills_from_jd(jd_text: str) -> Tuple[List[str], List[str]]:
    """
    Extract required vs nice-to-have skills from JD text.
    Returns: (required_skills, nice_to_have_skills)
    """
    # Find nice-to-have section
    nice_patterns = [
        r'nice.to.have[:\s]+(.*?)(?=required|must|$)',
        r'preferred[:\s]+(.*?)(?=required|must|$)',
        r'plus if you have[:\s]+(.*?)(?=required|must|$)',
        r'bonus[:\s]+(.*?)(?=required|must|$)',
    ]
    
    nice_text = ""
    for pattern in nice_patterns:
        m = re.search(pattern, jd_text.lower(), re.DOTALL)
        if m:
            nice_text = m.group(1)
            break
    
    all_skills = extract_skills_from_text(jd_text)
    nice_skills = extract_skills_from_text(nice_text) if nice_text else []
    required_skills = [s for s in all_skills if s not in nice_skills]
    
    return required_skills, nice_skills
