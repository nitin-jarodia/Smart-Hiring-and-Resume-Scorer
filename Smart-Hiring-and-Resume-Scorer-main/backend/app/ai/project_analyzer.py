import re
from typing import List, Dict, Any
import logging
from .skill_extractor import extract_skills_from_text
from .embeddings import embed_text, cosine_similarity

logger = logging.getLogger(__name__)

def extract_project_sections(resume_text: str) -> List[str]:
    """
    Naively extract blocks of text that likely represent 'Projects'.
    Looks for the "Projects" section and splits by bullet points or common separators.
    """
    text_lower = resume_text.lower()
    
    # Try to find exactly where the projects section starts and ends
    project_idx = text_lower.find("project")
    if project_idx == -1:
        return []
        
    # Heuristic: limit the project section to the next major heading
    next_headings = ["experience", "education", "skills", "certifications", "summary"]
    end_idx = len(text_lower)
    
    for heading in next_headings:
        idx = text_lower.find(heading, project_idx + 10)
        if idx != -1 and idx < end_idx:
            # Check if it's likely a heading (has newlines around it)
            if '\n' in text_lower[idx-5:idx+len(heading)+5]:
                end_idx = idx

    project_block = resume_text[project_idx:end_idx]
    
    # Try to split into individual projects (heuristic: bullet points, numbered lists, or double newlines)
    # Recognize patterns like "1. Project Name", "* Project Name", "BOLD PROJECT NAME"
    chunks = re.split(r'\n(?:\d+\.|\*|\u2022|[\u25cf\u25cb\u25aa\u25ab])|\n\s*\n', project_block)
    
    valid_chunks = [c.strip() for c in chunks if len(c.strip()) > 30]
    return valid_chunks

def evaluate_complexity(project_text: str) -> str:
    """Evaluate complexity based on technical keywords and depth of description."""
    text_lower = project_text.lower()
    
    high_complexity_flags = ["architecture", "microservices", "machine learning", "distributed", "kubernetes", "cloud", "optimization", "system design", "scale", "concurrency", "nlp", "transformers"]
    med_complexity_flags = ["database", "api", "integration", "full-stack", "react", "node", "deployment", "authentication", "dashboard", "frontend", "backend"]
    
    high_count = sum(1 for flag in high_complexity_flags if flag in text_lower)
    med_count = sum(1 for flag in med_complexity_flags if flag in text_lower)
    
    word_count = len(project_text.split())
    
    if high_count >= 2 and word_count > 40:
        return "High"
    elif (high_count == 1 or med_count >= 3) and word_count > 25:
        return "Medium"
    else:
        return "Low"

def evaluate_impact(project_text: str) -> int:
    """Estimate impact score (0-100) based on quantifiable metrics."""
    score = 45 # Base score bumped
    
    # Check for numbers/percentages
    percentages = re.findall(r'(\d+(?:\.\d+)?)%', project_text)
    numbers = re.findall(r'\b(\d{2,})\b', project_text) # e.g. 50, 1000
    dollar_amounts = re.findall(r'\$\d+', project_text)
    
    if percentages: score += 20 * min(2, len(percentages))
    if numbers: score += 10 * min(2, len(numbers))
    if dollar_amounts: score += 25
    
    impact_words = ["resulted in", "achieved", "improved", "reduced", "increased", "optimized", "saved", "impact", "delivered"]
    for word in impact_words:
        if word in project_text.lower():
            score += 15
            
    return min(100, score)

def evaluate_projects(resume_text: str, jd_text: str) -> List[Dict[str, Any]]:
    """
    Evaluates projects found in the resume against the provided Job Description.
    """
    jd_skills = extract_skills_from_text(jd_text)
    jd_emb = embed_text(jd_text)
    
    project_chunks = extract_project_sections(resume_text)
    evaluations = []
    
    for chunk in project_chunks[:5]: # Limit to top 5 projects
        # 1. Project Name Estimation (first few words or before a colon)
        # Handle "Project Name: describing the project..."
        first_line = chunk.split('\n')[0].strip()
        if ':' in first_line and len(first_line.split(':')[0]) < 40:
            name = first_line.split(':')[0]
        else:
            name = first_line[:40]

        # Clean up
        name = re.sub(r'(?i)^(?:projects?|personal projects?|academic projects?)\s*[:\-]?\s*', '', name).strip()
        name = re.sub(r'^\d+\.\s*|\*\s*', '', name).strip()
        
        if len(name) < 3 or name.lower() in ["projects", "personal projects"]:
            name = "Project " + str(len(evaluations) + 1)
            
        # 2. Technologies Used
        tech_used = extract_skills_from_text(chunk)
        
        # 3. Complexity
        complexity = evaluate_complexity(chunk)
        
        # 4. Impact Score
        impact_score = evaluate_impact(chunk)
        
        # 5. Relevance to Job
        proj_emb = embed_text(chunk)
        relevance_sim = cosine_similarity(jd_emb, proj_emb)
        relevance = min(100, max(0, int((relevance_sim - 0.1) / 0.7 * 100)))
        
        if not tech_used and len(chunk) < 60:
            continue # Likely not a real project chunk
            
        evaluations.append({
            "project_name": name,
            "description_snippet": chunk[:150] + "...",
            "complexity_level": complexity,
            "core_technologies": tech_used,
            "innovation_impact_score": impact_score,
            "relevance_to_job": relevance,
            "suggestions": generate_project_suggestions(chunk, jd_skills, impact_score)
        })
        
    return evaluations

def generate_project_suggestions(project_text: str, jd_skills: List[str], impact_score: int) -> List[str]:
    suggestions = []
    
    # Check if impact is low
    if impact_score < 60:
        suggestions.append("Add measurable outcomes (e.g., 'Improved performance by 20%') to strengthen the impact.")
        
    # Check for JD skill overlap
    tech_used = extract_skills_from_text(project_text)
    missing_jd_skills = [s for s in jd_skills[:5] if s.lower() not in [t.lower() for t in tech_used]]
    
    if missing_jd_skills and len(tech_used) > 0:
        suggestions.append(f"If applicable, explicitly mention how this project utilized any of these job requirements: {', '.join(missing_jd_skills[:2])}.")
        
    if "led" not in project_text.lower() and "managed" not in project_text.lower():
        suggestions.append("Clarify your specific role and leadership contributions in this project.")
        
    return suggestions[:2]
