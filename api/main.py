# ──────────────────────────────────────────────────────────────
# PURPOSE: FastAPI application with API key authentication
# ──────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from api.database import init_db, save_application, get_all_applications
from writer.scorer import score_job
from writer.cover_letter import generate_cover_letter

# ── API KEY SETUP ─────────────────────────────────────────────

# Read the secret key from .env
AGENT_API_KEY = os.getenv("AGENT_API_KEY")

# This tells FastAPI to look for a header called "X-API-Key"
# auto_error=False means we handle the error ourselves below
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    FastAPI calls this automatically on protected endpoints.
    
    If the header is missing or wrong → returns 403 Forbidden
    If the header matches .env key   → allows the request
    """
    if not api_key or api_key != AGENT_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Add X-API-Key header."
        )
    return api_key


# ── APP SETUP ─────────────────────────────────────────────────

app = FastAPI(
    title="AI Job Agent API",
    description="Scores jobs and generates cover letters using RAG + LLM",
    version="1.0.0"
)

init_db()


# ── REQUEST MODELS ────────────────────────────────────────────

class JobRequest(BaseModel):
    job_title:       str
    company:         str
    job_description: str


class FullPipelineRequest(BaseModel):
    job_title:       str
    company:         str
    job_description: str
    auto_save:       bool = True


# ── ENDPOINTS ─────────────────────────────────────────────────

# PUBLIC — no key needed
# Anyone can check if the API is alive
@app.get("/")
def root():
    return {
        "status": "running",
        "message": "AI Job Agent API is live",
        "endpoints": ["/score", "/cover-letter", "/process", "/applications"]
    }


# PROTECTED — key required
# Scoring reveals your profile details
@app.post("/score")
def score_endpoint(
    request: JobRequest,
    api_key: str = Security(verify_api_key)
):
    try:
        result = score_job(request.job_description)
        result["job_title"] = request.job_title
        result["company"]   = request.company
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PROTECTED — key required
# Generates letters using your private resume data
@app.post("/cover-letter")
def cover_letter_endpoint(
    request: JobRequest,
    api_key: str = Security(verify_api_key)
):
    try:
        result = generate_cover_letter(
            job_description=request.job_description,
            company_name=request.company,
            job_title=request.job_title
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PROTECTED — key required
# Main pipeline — most sensitive endpoint
@app.post("/process")
def full_pipeline(
    request: FullPipelineRequest,
    api_key: str = Security(verify_api_key)
):
    try:
        score_result = score_job(request.job_description)

        response = {
            "job_title":       request.job_title,
            "company":         request.company,
            "score":           score_result["score"],
            "verdict":         score_result["verdict"],
            "apply":           score_result["apply"],
            "matching_skills": score_result.get("matching_skills", []),
            "missing_skills":  score_result.get("missing_skills", []),
            "cover_letter":    None,
            "saved_id":        None
        }

        if score_result["apply"]:
            letter_result = generate_cover_letter(
                job_description=request.job_description,
                company_name=request.company,
                job_title=request.job_title
            )
            response["cover_letter"] = letter_result["cover_letter"]

        if request.auto_save:
            saved_id = save_application({
                "job_title":       request.job_title,
                "company":         request.company,
                "job_description": request.job_description,
                "score":           score_result["score"],
                "verdict":         score_result["verdict"],
                "matching_skills": score_result.get("matching_skills", []),
                "missing_skills":  score_result.get("missing_skills", []),
                "cover_letter":    response["cover_letter"],
                "apply":           score_result["apply"]
            })
            response["saved_id"] = saved_id

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# PROTECTED — key required
# Contains your personal application history
@app.get("/applications")
def get_applications(
    api_key: str = Security(verify_api_key)
):
    try:
        applications = get_all_applications()
        return {
            "total": len(applications),
            "applications": applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))