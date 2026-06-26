import re
from typing import List, Dict

def detect_resume_fraud(text: str, skills: List[str]) -> List[Dict[str, str]]:
    """
    Analyzes resume text and extracted skills to identify potential fraud,
    embellishment, or 'white fonting' (keyword stuffing).
    Returns a list of warnings (each a dict with 'reason' and 'severity').
    """
    flags = []
    text_lower = text.lower()
    word_count = len(text.split())

    # 1. Keyword Stuffing / "White Fonting" Detection
    # If the ratio of skills to total words is extremely high, it might be stuffed.
    if word_count > 0:
        skill_density = len(skills) / word_count
        if skill_density > 0.15: # e.g. more than 15% of the resume is just raw skill keywords
            flags.append({
                "reason": f"Suspiciously high skill density ({len(skills)} skills in {word_count} words). Possible keyword stuffing or hidden text.",
                "severity": "High"
            })
    
    if len(skills) > 40:
        flags.append({
            "reason": f"Excessive number of technical skills listed ({len(skills)}). May indicate keyword stuffing.",
            "severity": "Medium"
        })

    # 2. Invisible text patterns (repeated keywords string at end or start, sometimes parsed as blocks)
    # Simple heuristic: looking for 4+ consecutive commas with only single words between them in a massive block.
    if re.search(r'(\b\w+\b\s*,\s*){20,}', text):
         flags.append({
            "reason": "Large block of comma-separated words detected. Verify this is legitimate and not SEO keyword stuffing.",
            "severity": "Medium"
         })

    # 3. Known "Degree Mills" or suspicious terms
    suspicious_terms = [
        "diploma mill", "life experience degree", "purchased degree",
        "almeda university", "ashwood university", "belford university",
        "columbiana university", "corley university", "rochville university"
    ]
    
    found_suspicious = [term for term in suspicious_terms if term in text_lower]
    if found_suspicious:
        flags.append({
            "reason": f"Suspicious educational institution or term detected: {', '.join(found_suspicious)}.",
            "severity": "High"
        })

    # 4. Impossible/Unrealistic Timelines (Basic check for conflicting dates)
    # E.g. claiming 20 years experience for a newly emerging technology (like ChatGPT/GenAI which started mainstream late 2022).
    recent_tech = {
        "chatgpt": 2022,
        "genai": 2022,
        "gpt-4": 2023,
        "next.js 14": 2023
    }
    
    for tech, year in recent_tech.items():
        if tech in text_lower:
            # Look for claims like "5 years of experience in ChatGPT"
            # Regex: (digit) (years|yrs) (.*) tech
            match = re.search(rf'(\d+)\+?\s*(?:years|yrs)\s*(?:of\s*experience)?\s*(?:in|with|using)?\s*.*?\b{re.escape(tech)}\b', text_lower)
            if match:
                years_claimed = int(match.group(1))
                current_year = 2024 # Context year
                max_possible = current_year - year + 1 # +1 gives them benefit of doubt
                if years_claimed > max_possible:
                    flags.append({
                        "reason": f"Unrealistic experience claimed: {years_claimed} years with {tech} (technology is newer than claimed experience).",
                        "severity": "High"
                    })

    # 5. Skill Duplication / Repeated Keywords
    # Counting occurrences of each skill in the raw text
    for skill in set(skills):
        if len(skill) < 3: continue
        count = text_lower.count(skill.lower())
        if count > 4: # Suspect if a technical term is repeated 5+ times in a short doc
             flags.append({
                "reason": f"High repetition of keyword '{skill}' ({count} times). Common tactic for invisible 'white font' keyword stuffing.",
                "severity": "Medium"
            })

    # 6. Extreme Buzzword Density (Short resume, many skills)
    if word_count < 150 and len(skills) > 10:
        flags.append({
            "reason": "Extreme buzzword-to-content ratio. Resume is very short but lists many technical skills. May lack depth or be AI-generated.",
            "severity": "High"
        })

    return flags
