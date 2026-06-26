from typing import Optional, List
from ..config import settings
import logging
logger = logging.getLogger(__name__)

def has_openai() -> bool:
    return bool(settings.OPENAI_API_KEY)

async def llm_explain_score(
    resume_text: str,
    jd_text: str,
    score: float,
    matched_skills: List[str],
    missing_skills: List[str],
    template_explanation: str
) -> str:
    """Generate LLM explanation or fall back to template."""
    if not has_openai():
        return template_explanation
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""You are an expert technical recruiter. Analyze this resume vs job description match.

Score: {score}/100
Matched skills: {', '.join(matched_skills[:10])}
Missing skills: {', '.join(missing_skills[:5])}

Job Description (excerpt):
{jd_text[:800]}

Resume (excerpt):
{resume_text[:800]}

Write a 3-4 sentence professional assessment of this candidate's fit for this role. Be specific, evidence-based, and constructive. Focus on technical alignment and experience match."""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"LLM explain failed: {e}")
        return template_explanation

async def llm_rewrite_bullets(resume_text: str, job_title: str) -> List[str]:
    """Rewrite resume bullets to be more impactful."""
    if not has_openai():
        return [
            "Use the STAR format: Situation → Task → Action → Result",
            "Start each bullet with a strong action verb (Led, Built, Reduced, Achieved)",
            "Quantify impact: include percentages, dollar amounts, time saved, or scale metrics",
            "Focus on outcomes over responsibilities",
        ]
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        prompt = f"""Extract 3 weak resume bullets from this resume and rewrite them as impactful, quantified STAR-format bullets for a {job_title} role.

Resume:
{resume_text[:1500]}

Format your response as:
ORIGINAL: [original bullet]
IMPROVED: [rewritten bullet]

(repeat for 3 bullets)"""

        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.5,
        )
        content = response.choices[0].message.content.strip()
        lines = [l for l in content.split('\n') if l.strip()]
        return lines[:8]
    except Exception as e:
        logger.error(f"LLM rewrite failed: {e}")
        return ["Use the STAR format for bullet points", "Quantify your achievements with metrics"]
