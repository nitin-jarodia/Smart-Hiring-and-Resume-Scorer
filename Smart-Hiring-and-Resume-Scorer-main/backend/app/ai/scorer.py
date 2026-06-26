import re
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging
logger = logging.getLogger(__name__)
from .parser import parse_years_of_experience, mask_pii, detect_sections
from .skill_extractor import extract_skills_from_text, compare_skills
from .embeddings import embed_text, cosine_similarity, get_top_evidence_chunks
from .project_analyzer import evaluate_projects
from .fraud_detector import detect_resume_fraud

SENIORITY_LEVELS = {
    "intern": (0, 1),
    "junior": (1, 3),
    "mid": (3, 6),
    "senior": (6, 12),
    "staff": (12, 20),
    "principal": (20, 50),
}

def estimate_seniority(years: int, text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ["principal engineer", "distinguished", "fellow"]):
        return "Principal"
    if any(w in text_lower for w in ["staff engineer", "vp ", "director", "head of", "engineering manager"]):
        return "Staff/Lead"
    senior_keywords = ["senior", "sr.", "sr ", "lead engineer", "tech lead", "principal"]
    if years >= 6 or any(w in text_lower for w in senior_keywords):
        return "Senior"
    if years >= 3 or "mid-level" in text_lower or "mid level" in text_lower:
        return "Mid"
    if years >= 1 or "junior" in text_lower or "associate" in text_lower:
        return "Junior"
    return "Intern/Entry"

def check_red_flags(text: str, years_exp: int, required_skills: List[str]) -> List[str]:
    flags = []
    
    # Job hopping: multiple short stints
    date_pattern = r'(\d{4})\s*[-–]\s*(\d{4}|\bpresent\b|\bcurrent\b)'
    dates = re.findall(date_pattern, text.lower())
    short_stints = 0
    for start, end in dates:
        try:
            s = int(start)
            e = datetime.now().year if end in ["present", "current"] else int(end)
            if 0 < (e - s) < 2:
                short_stints += 1
        except:
            pass
    if short_stints >= 3:
        flags.append("Frequent job changes (3+ positions under 2 years)")
    
    # Check experience gap patterns
    if years_exp == 0 and len(text) < 500:
        flags.append("Very limited resume content detected")
    
    return flags

def find_skill_evidence(text: str, skills: List[str]) -> List[Dict[str, str]]:
    """Find sentences in resume that contain matched skills."""
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    evidence = []
    seen_skills = set()
    
    for skill in skills[:8]:  # Limit evidence snippets
        if skill in seen_skills:
            continue
        for sentence in sentences:
            if skill.lower() in sentence.lower() and len(sentence.strip()) > 20:
                evidence.append({
                    "skill": skill,
                    "excerpt": sentence.strip()[:250],
                    "type": "skill_match"
                })
                seen_skills.add(skill)
                break
    
    return evidence

def generate_recommendations(missing_skills: List[str], score: float, seniority: str) -> List[str]:
    recs = []
    
    if missing_skills:
        top_missing = missing_skills[:5]
        for skill in top_missing:
            recs.append(f"If you have experience with {skill}, consider adding it with specific examples and metrics to your resume.")
    
    if score < 50:
        recs.append("Rewrite experience bullets using the STAR format (Situation, Task, Action, Result) with quantifiable outcomes.")
        recs.append("Include a strong professional summary tailored to this specific role.")
    
    if score < 70:
        recs.append("Optimize for ATS: use exact keywords from the job description in context throughout your resume.")
        recs.append("Ensure skills section uses exact terminology from the job posting.")
    
    recs.append("Quantify achievements where possible (e.g., 'Reduced load time by 40%' instead of 'Improved performance').")
    
    return recs[:6]

def generate_interview_questions(missing_skills: List[str], jd_text: str, seniority: str) -> List[Dict[str, str]]:
    questions = []
    
    # Questions based on missing skills
    for skill in missing_skills[:3]:
        questions.append({
            "question": f"Can you describe your experience with {skill} or similar technologies? How would you approach learning it quickly?",
            "focus_area": f"Skill gap: {skill}",
            "good_answer_signal": f"Candidate demonstrates adaptability, shows related experience, or presents a concrete learning plan for {skill}."
        })
    
    # General behavioral questions
    behavioral = [
        {
            "question": "Describe a technically complex project you led end-to-end. What was your approach and outcome?",
            "focus_area": "Technical depth & ownership",
            "good_answer_signal": "Specific technical details, clear problem-solving approach, measurable outcomes, acknowledgment of tradeoffs."
        },
        {
            "question": "Tell me about a time you disagreed with a technical decision. How did you handle it?",
            "focus_area": "Collaboration & communication",
            "good_answer_signal": "Constructive approach, data-driven arguments, ability to commit even when overruled."
        },
        {
            "question": "How do you approach debugging a production issue you've never seen before?",
            "focus_area": "Problem-solving methodology",
            "good_answer_signal": "Systematic approach, use of logs/metrics/tracing, calm under pressure, post-mortem mindset."
        },
    ]
    questions.extend(behavioral[:5 - len(questions)])
    
    return questions[:7]

def generate_strength_tags(
    score: float, 
    matched_skills: List[str], 
    missing_skills: List[str], 
    fraud_flags: List[Dict],
    seniority: str
) -> List[str]:
    """Generate high-level summary tags for the candidate."""
    tags = []
    
    # Skill-based tags
    if len(matched_skills) >= 5:
        tags.append("Strong Skillset")
    for s in matched_skills[:2]:
        tags.append(f"Expert: {s.capitalize()}")
        
    # Seniority tags
    tags.append(f"Level: {seniority}")
    
    # Gap/Risk tags
    if not fraud_flags:
        tags.append("Low Risk")
    else:
        high_risk = any(f.get('severity') == 'High' for f in fraud_flags)
        tags.append("High Risk" if high_risk else "Medium Risk")
        
    if len(missing_skills) > 5:
        tags.append("Skill Gaps")
        
    if score > 80:
        tags.append("Top Match")
    elif score > 60:
        tags.append("Good Fit")
        
    return tags[:5]

def generate_explanation(
    score: float, breakdown: Dict, matched_skills: List[str],
    missing_skills: List[str], seniority: str, candidate_name: str = "Candidate"
) -> str:
    """Generate a high-quality, recruiter-friendly narrative explanation."""
    level = "shows exceptional" if score >= 85 else "shows strong" if score >= 70 else "shows moderate" if score >= 50 else "shows limited"
    
    matched_top = ", ".join(matched_skills[:3]) if matched_skills else "none of the core"
    gap_top = ", ".join(missing_skills[:3]) if missing_skills else "no critical"
    
    narrative = (
        f"{candidate_name} {level} alignment for this {seniority} role. "
        f"They demonstrate solid expertise in {matched_top}. "
    )
    
    if missing_skills:
        narrative += f"However, notice some gaps in {gap_top}, which might require training. "
    else:
        narrative += "Their profile perfectly matches the technical requirements of the job description. "
        
    narrative += f"Overall, they achieved a score of {score:.0f}/100, driven by "
    
    best_part = max(
        [("semantic relevance", breakdown.get('semantic_similarity', 0)),
         ("skill matching", breakdown.get('skill_match', 0)),
         ("experience alignment", breakdown.get('experience_alignment', 0))],
        key=lambda x: x[1]
    )
    
    narrative += f"high {best_part[0]} ({best_part[1]:.0f}%)."
    
    return narrative

def score_resume(jd_text: str, resume_text: str, jd_skills: List[str] = None) -> Dict[str, Any]:
    """
    Main scoring function. Returns full analysis for a resume vs JD.
    Weights: semantic 40%, skills 35%, experience 15%, education 5%, formatting 5%
    """
    # Mask PII for fair scoring
    clean_resume = mask_pii(resume_text)
    clean_jd = mask_pii(jd_text)
    
    # 1. Semantic similarity (40%)
    jd_emb = embed_text(clean_jd)
    resume_emb = embed_text(clean_resume)
    semantic_sim = cosine_similarity(jd_emb, resume_emb)
    # Normalize: cosine is typically 0.1-0.9 for real docs, scale to 0-100
    semantic_score = min(100, max(0, (semantic_sim - 0.1) / 0.7 * 100))
    
    # 2. Skill matching (35%)
    if jd_skills is None:
        jd_skills = extract_skills_from_text(jd_text)
    resume_skills = extract_skills_from_text(resume_text)
    matched_skills, missing_skills, skill_ratio = compare_skills(jd_skills, resume_skills)
    skill_score = skill_ratio * 100
    
    # 3. Experience alignment (15%)
    years_exp = parse_years_of_experience(resume_text)
    jd_years_match = re.search(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', jd_text.lower())
    required_years = int(jd_years_match.group(1)) if jd_years_match else 2
    
    exp_score = min(100, (years_exp / max(required_years, 1)) * 100) if years_exp > 0 else 30
    
    # 4. Education alignment (5%)
    edu_keywords = ["bachelor", "master", "phd", "degree", "b.s.", "m.s.", "b.e.", "b.tech", "m.tech"]
    edu_score = 70 if any(k in resume_text.lower() for k in edu_keywords) else 40
    if "phd" in resume_text.lower() or "doctorate" in resume_text.lower():
        edu_score = 95
    
    # 5. Formatting/clarity (5%)
    sections = detect_sections(resume_text)
    section_count = len([s for s in sections if s not in ["header"]])
    format_score = min(100, section_count * 15)
    
    # Weighted total
    total_score = (
        semantic_score * 0.40 +
        skill_score * 0.35 +
        exp_score * 0.15 +
        edu_score * 0.05 +
        format_score * 0.05
    )
    total_score = round(min(100, max(0, total_score)), 1)
    
    # Confidence: based on resume length + skill coverage
    confidence = min(1.0, len(resume_text) / 2000 * 0.5 + skill_ratio * 0.5)
    
    # Seniority
    seniority = estimate_seniority(years_exp, resume_text)
    
    # Evidence
    evidence_from_skills = find_skill_evidence(resume_text, matched_skills)
    top_chunks = get_top_evidence_chunks(resume_text, jd_text, top_k=2)
    for chunk, sim in top_chunks:
        evidence_from_skills.append({
            "skill": "semantic_match",
            "excerpt": chunk[:250],
            "type": "semantic_relevance",
            "score": round(sim * 100, 1)
        })
    
    # Nice-to-have skills from JD
    nice_to_have = []  # Would be populated from JD analysis
    
    # Red flags
    red_flags = check_red_flags(resume_text, years_exp, jd_skills)
    
    # Recommendations
    recommendations = generate_recommendations(missing_skills, total_score, seniority)
    
    # Interview questions
    interview_questions = generate_interview_questions(missing_skills, jd_text, seniority)
    
    # Project Evaluations
    project_evaluations = evaluate_projects(resume_text, jd_text)
    
    # Fraud Detection
    fraud_flags = detect_resume_fraud(resume_text, matched_skills + missing_skills)
    
    # Tags
    strength_tags = generate_strength_tags(
        total_score,
        matched_skills,
        missing_skills,
        fraud_flags,
        seniority
    )
    
    breakdown = {
        "semantic_similarity": round(semantic_score, 1),
        "skill_match": round(skill_score, 1),
        "experience_alignment": round(exp_score, 1),
        "education_alignment": round(edu_score, 1),
        "formatting_clarity": round(format_score, 1),
        "weights": {
            "semantic_similarity": 0.40,
            "skill_match": 0.35,
            "experience_alignment": 0.15,
            "education_alignment": 0.05,
            "formatting_clarity": 0.05,
        }
    }

    # Explanation
    explanation = generate_explanation(
        total_score,
        breakdown,
        matched_skills,
        missing_skills,
        seniority
    )
    
    return {
        "score": total_score,
        "confidence": round(confidence, 2),
        "seniority": seniority,
        "breakdown": breakdown,
        "evidence": evidence_from_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "nice_to_have_found": nice_to_have,
        "red_flags": red_flags,
        "fraud_flags": fraud_flags,
        "recommendations": recommendations,
        "interview_questions": interview_questions,
        "project_evaluations": project_evaluations,
        "explanation": explanation,
        "strength_tags": strength_tags,
    }


def generate_resume_tips(text: str, sections: dict, skills: List[str]) -> List[Dict[str, str]]:
    """Generate high-quality, professional, and actionable resume improvement tips."""
    tips = []
    text_lower = text.lower()
    word_count = len(text.split())
    
    # 1. Formatting & Readability (Length & Structure)
    if word_count < 250:
        tips.append({
            "category": "Content Depth", 
            "tip": "Your resume is too brief. Expand on your professional experience by detailing the scope of your projects, specific responsibilities, and the technologies you utilized. Aim for comprehensive 3-5 bullet points per role.", 
            "impact": "High"
        })
    elif word_count > 1000:
        tips.append({
            "category": "Brevity & Focus", 
            "tip": "Your resume is excessively long, risk losing the recruiter's attention. Condense your older roles and focus on the accomplishments most directly relevant to your target positions. Aim for 1-2 pages maximum.", 
            "impact": "Medium"
        })

    # 2. Key Sections
    section_names = [s.lower() for s in (sections.keys() if isinstance(sections, dict) else [])]
    expected_sections = {"summary": "Professional Summary", "experience": "Work Experience", "education": "Education Background"}
    for key, formal_name in expected_sections.items():
        if not any(key in s for s in section_names):
            if key == "summary":
                tips.append({
                    "category": "Missing Key Section", 
                    "tip": "Add a crisp, 3-4 line Professional Summary at the top. Use this to immediately establish your professional identity, highlight your top 2-3 most impressive career achievements, and state your value proposition.", 
                    "impact": "High"
                })
            else:
                tips.append({
                    "category": "Missing Key Section", 
                    "tip": f"Your resume lacks a clearly defined '{formal_name}' section. Ensure you use standard, identifiable headings so Application Tracking Systems (ATS) can parse your history correctly.", 
                    "impact": "High"
                })

    # 3. Measurable Achievements
    number_pattern = re.compile(r'\b\d+(?:%|k|m|b|\+)?\b', re.IGNORECASE)
    numbers_found = len(number_pattern.findall(text))
    if numbers_found < 3:
        example_sentence = ""
        sentences = re.split(r'(?<=[.!?\n])\s+', text)
        for s in sentences:
            if len(s.split()) >= 8 and not number_pattern.search(s) and any(verb in s.lower() for verb in ["developed", "created", "built", "managed", "led"]):
                example_sentence = s.strip().replace("\n", " ")
                if len(example_sentence) > 80:
                    example_sentence = example_sentence[:77] + "..."
                break
                
        tip_text = "Your bullet points describe responsibilities rather than achievements. "
        if example_sentence:
            tip_text += f"For example, you wrote: '{example_sentence}'. Try quantifying your impact using metrics (e.g., '...resulting in a 40% loading time decrease'). Numbers provide concrete proof of your capabilities."
        else:
            tip_text += "Quantify your impact using metrics (e.g., 'Decreased loading time by 40%', or 'Led a team of 6'). Numbers provide concrete proof."
            
        tips.append({
            "category": "Measurable Impact", 
            "tip": tip_text, 
            "impact": "Critical"
        })

    # 4. Action Verbs & Bullet Pacing
    weak_words = ["helped", "worked on", "responsible for", "assisted", "did", "made"]
    used_weak = [w for w in weak_words if w in text_lower]
    if len(used_weak) >= 2:
        example_sentence = ""
        sentences = re.split(r'(?<=[.!?\n])\s+', text)
        for s in sentences:
            if used_weak[0] in s.lower() and len(s) > 15:
                example_sentence = s.strip().replace("\n", " ")
                if len(example_sentence) > 80:
                    example_sentence = example_sentence[:77] + "..."
                break
                
        tip_text = f"Avoid passive phrases like '{used_weak[0]}'. "
        if example_sentence:
            tip_text += f"For instance, instead of '{example_sentence}', start the bullet point with a strong, active verb (e.g., 'Spearheaded', 'Architected', 'Optimized')."
        else:
            tip_text += "Start every bullet point with strong, active verbs (e.g., 'Spearheaded', 'Architected', 'Optimized', 'Delivered')."
            
        tip_text += " This frames you as a proactive driver of results rather than a passive participant."
        
        tips.append({
            "category": "Action-Oriented Language", 
            "tip": tip_text, 
            "impact": "High"
        })

    # 5. Clarity in Project Descriptions
    if "project" in text_lower or any("project" in s for s in section_names):
        if not any(c in text_lower for c in ["resulted in", "achieved", "improved", "reduced", "increased"]):
            tips.append({
                "category": "Project Outcomes", 
                "tip": "Your project descriptions focus heavily on the 'what' but lack the 'so what'. For every major project listed, explicitly state the final business or technical outcome. What was the ROI? How did it improve the user experience?", 
                "impact": "Medium"
            })
    else:
        # If no project section for junior/mid
        years_exp = parse_years_of_experience(text)
        if years_exp < 3:
            tips.append({
                "category": "Showcase Projects", 
                "tip": "Since you have fewer than 3 years of formal experience, adding a dedicated 'Projects' section highlighting relevant academic, personal, or open-source work will significantly strengthen your profile.", 
                "impact": "High"
            })

    # 6. Skill Presentation
    if len(skills) < 8:
        tips.append({
            "category": "Skill Presentation", 
            "tip": "Your resume's technical skill footprint is very light. Ensure you have a dedicated 'Skills' section listing the core languages, frameworks, and methodologies you know. This is crucial for getting past automated ATS filters.", 
            "impact": "High"
        })
    elif len(skills) > 30:
        tips.append({
            "category": "Targeted Skills", 
            "tip": "You've listed an overwhelming number of skills, which dilutes your core expertise. Group your skills logically (e.g., 'Languages', 'Frameworks', 'Tools') and remove outdated or irrelevant technologies.", 
            "impact": "Low"
        })

    # 7. Basic Hygiene
    has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+', text))
    has_contact = bool(re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text))
    if not (has_email and has_contact):
        tips.append({
            "category": "Contact Information", 
            "tip": "Your resume is missing clear contact information (Email and Phone Number). Ensure this is prominently displayed at the very top of your document.", 
            "impact": "Critical"
        })

    if "linkedin" not in text_lower:
        tips.append({
            "category": "Professional Presence", 
            "tip": "Include a link to your LinkedIn profile. Modern recruiters almost always cross-reference resumes with LinkedIn to look for endorsements, mutual connections, and a broader professional history.", 
            "impact": "Medium"
        })

    # Excellent fallback
    if len(tips) < 2:
        tips.append({
            "category": "General Impression", 
            "tip": "Your resume is extremely well-structured! You have clearly quantified achievements, excellent action verbs, and clear sections. Continue to tailor the specific keywords to match each job description you apply for.", 
            "impact": "Low"
        })

    return tips


def analyze_general_profile(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume without a specific Job Description.
    Calculates a 'Market Readiness' score and estimates seniority.
    """
    # 1. Basic metrics
    years_exp = parse_years_of_experience(resume_text)
    seniority = estimate_seniority(years_exp, resume_text)
    skills = extract_skills_from_text(resume_text)
    sections = detect_sections(resume_text)
    
    # 2. Market Readiness Score (0-100)
    # Experience (40%)
    exp_score = min(100, (years_exp / 10) * 100) if years_exp > 0 else 20
    # Skill Breadth (40%)
    skill_score = min(100, (len(skills) / 15) * 100)
    # Formatting/Structure (20%)
    format_score = min(100, len(sections) * 15)
    
    total_score = (exp_score * 0.4) + (skill_score * 0.4) + (format_score * 0.2)
    total_score = round(total_score, 1)
    
    # 3. Breakdown
    breakdown = {
        "experience_depth": round(exp_score, 1),
        "skill_breadth": round(skill_score, 1),
        "presentation_quality": round(format_score, 1),
        "total": total_score
    }
    
    # 4. Strength Tags
    tags = generate_strength_tags(total_score, skills[:5], [], [], seniority)
    
    # 5. Explanation
    explanation = (
        f"Your profile reflects a {seniority} level of expertise with strong foundatons in {', '.join(skills[:3])}. "
        f"With an overall market readiness score of {total_score:.0f}, you have a solid professional presence."
    )
    
    return {
        "score": total_score,
        "seniority": seniority,
        "breakdown": breakdown,
        "strength_tags": tags,
        "explanation": explanation,
        "extracted_skills": skills,
    }

