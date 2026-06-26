import httpx
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..models.domain import CandidateGitHub

logger = logging.getLogger(__name__)

async def fetch_github_data(username: str) -> Dict[str, Any]:
    """Fetch user profile and public repos from GitHub."""
    data = {
        "username": username,
        "valid": False,
        "metrics": {"followers": 0, "public_repos": 0, "total_stars": 0},
        "top_languages": {}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Fetch user profile
            user_resp = await client.get(f"https://api.github.com/users/{username}", timeout=10.0)
            if user_resp.status_code != 200:
                logger.warning(f"GitHub user {username} not found or rate limited.")
                return data
                
            user_json = user_resp.json()
            data["valid"] = True
            data["metrics"]["followers"] = user_json.get("followers", 0)
            data["metrics"]["public_repos"] = user_json.get("public_repos", 0)
            
            # Fetch repositories to calculate stars and languages
            repos_resp = await client.get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated", timeout=15.0)
            if repos_resp.status_code == 403:
                logger.warning(f"GitHub API Rate Limit hit for {username} when fetching repos.")
                data["error"] = "GitHub API Rate Limit. Please try again later."
                return data
            elif repos_resp.status_code != 200:
                logger.warning(f"Failed to fetch repositories for {username}: {repos_resp.status_code}")
                data["error"] = f"Failed to fetch repositories for '{username}'."
                return data
            
            repos = repos_resp.json()
            if not repos:
                data["error"] = f"No public repositories found for user '{username}'."
                # Even if no repos, the user profile is valid, so we keep data["valid"] = True
                # but indicate no repos were found.
                return data
                
            total_stars = 0
            lang_counts = {}
            
            for r in repos:
                total_stars += r.get("stargazers_count", 0)
                lang = r.get("language")
                if lang:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
                    
            data["metrics"]["total_stars"] = total_stars
            
            # Sort languages descending
            sorted_langs = sorted(lang_counts.items(), key=lambda x: x[1], reverse=True)
            data["top_languages"] = {k: v for k, v in sorted_langs[:5]}
            
            # Top projects
            sorted_by_stars = sorted(repos, key=lambda x: x.get("stargazers_count", 0), reverse=True)
            top_projects = []
            for r in sorted_by_stars[:3]:
                top_projects.append({
                    "name": r.get("name"),
                    "description": r.get("description"),
                    "language": r.get("language"),
                    "stars": r.get("stargazers_count", 0),
                    "url": r.get("html_url")
                })
            data["metrics"]["top_projects"] = top_projects
                
                
    except Exception as e:
        logger.error(f"GitHub API Error for {username}: {e}")
        data["error"] = f"An unexpected error occurred: {e}"
        
    return data

async def analyze_and_store_github(db: Session, candidate_id: str, github_url: str):
    """Analyze GitHub profile and store/update in DB."""
    # Robustly extract username even from github.com/user/repo URLs
    try:
        parts = github_url.strip().strip("/").split("/")
        # Find the index of the github.com part
        gh_idx = next((i for i, p in enumerate(parts) if "github.com" in p), -1)
        if gh_idx == -1 or gh_idx + 1 >= len(parts):
            logger.error(f"Could not extract username from GitHub URL: {github_url}")
            return
        username = parts[gh_idx + 1].strip()
    except Exception:
        logger.error(f"Invalid GitHub URL format: {github_url}")
        return

    if not username:
        logger.error(f"Empty username extracted from GitHub URL: {github_url}")
        return
        
    github_data = await fetch_github_data(username)
    
    # If there's an error or it's not valid, we might still want to store the error message
    # or at least not proceed with storing incomplete/invalid data.
    # The `valid` flag now indicates if the user profile itself was found.
    # `error` provides more specific reasons.
    
    if not github_data["valid"] and github_data["error"]:
        logger.info(f"Not storing GitHub data for {username} due to: {github_data['error']}")
        # Optionally, you could store the error message in the DB if the model supports it.
        return 
        
    try:
        record = db.query(CandidateGitHub).filter(CandidateGitHub.candidate_id == candidate_id).first()
        if record:
            record.github_url = github_url
            record.username = username
            record.metrics = github_data["metrics"]
            record.top_languages = github_data["top_languages"]
            # If there was an error but valid is true (e.g., no repos), we might want to clear previous errors
            # or store the new error. For now, we assume if valid, we update.
        else:
            record = CandidateGitHub(
                candidate_id=candidate_id,
                github_url=github_url,
                username=username,
                metrics=github_data["metrics"],
                top_languages=github_data["top_languages"]
            )
            db.add(record)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed handling DB for GitHub analysis: {e}")
