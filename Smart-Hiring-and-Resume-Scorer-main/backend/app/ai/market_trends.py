from typing import List, Dict

GLOBAL_TRENDS = {
    "Cloud & DevOps": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD"],
    "AI & Data": ["Machine Learning", "PyTorch", "TensorFlow", "Generative AI", "Data Engineering"],
    "Frontend & UI": ["React", "Next.js", "TypeScript", "Tailwind CSS"],
    "Backend & Architecture": ["Python", "FastAPI", "Go", "Node.js", "Microservices"]
}

def get_market_trend_recommendations(candidate_skills: List[str]) -> List[Dict[str, str]]:
    """
    Identifies missing high-impact market trends based on the candidate's existing skills.
    If the candidate has some skills in a domain, we suggest the top trending skills in that domain.
    """
    candidate_skills_lower = set(s.strip().lower() for s in candidate_skills)
    suggestions = []

    # Map candidate skills to domains to see their interest
    domain_interest = {domain: 0 for domain in GLOBAL_TRENDS}
    
    for skill in candidate_skills_lower:
        for domain, trends in GLOBAL_TRENDS.items():
            if any(t.lower() in skill for t in trends) or any(skill in t.lower() for t in trends):
                domain_interest[domain] += 1
                
    # If no specific interest, default to generally good areas like Cloud or AI
    if sum(domain_interest.values()) == 0:
        domain_interest["Cloud & DevOps"] = 1
        domain_interest["AI & Data"] = 1

    # Suggest missing trends in their top domains
    sorted_domains = sorted(domain_interest.items(), key=lambda x: -x[1])
    
    for domain, interest in sorted_domains:
        if interest > 0 or len(suggestions) < 3:
            for trend in GLOBAL_TRENDS[domain]:
                if trend.lower() not in candidate_skills_lower:
                    if not any(s["skill"] == trend for s in suggestions):
                        suggestions.append({
                            "skill": f"{trend} 🚀",
                            "demand_count": 99,  # Artificial high demand to signify market trend
                            "priority": "high",
                            "reason": f"Global market trend in {domain}"
                        })
                if len(suggestions) >= 5:
                    break
        if len(suggestions) >= 5:
            break
            
    return suggestions
