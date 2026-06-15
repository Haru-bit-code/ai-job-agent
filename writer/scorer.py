# ──────────────────────────────────────────────────────────────
# PURPOSE: Score how relevant a job description is for Ansar
#          Uses Groq LLM to reason about the match
#          Returns a score 0-100 + reasons + verdict
# ──────────────────────────────────────────────────────────────

import json
import re
from writer.groq_client import ask_groq

# This is Ansar's profile — the scorer uses this as reference
# When you update your skills, update this. One place. 
CANDIDATE_PROFILE = """
Name: Ansar Kamal
Role Target: Data Analyst / Data Scientist / ML Engineer
Location: Kerala, India (open to remote)

Technical Skills:
- Languages: Python, SQL, HTML, CSS
- ML/AI: Scikit-learn, NLP, Sentiment Analysis, LangChain, RAG
- Data: Pandas, NumPy, EDA, Data Cleaning, Matplotlib, Seaborn
- Tools: FastAPI, SQLite, Git, GitHub, Jupyter, VS Code
- APIs: OpenAI API, Groq API, REST APIs

Projects Built:
- Customer Churn Prediction (ML classification)
- Statement Sentiment Analyzer (NLP)
- Expense Tracker with Trend Analysis
- Job Application Tracker (FastAPI + SQLite)
- Resume Screener (NLP automation)
- RAG Document Chatbot (LangChain + Vector DB)
- Weather Dashboard (REST API)

Education:
- MSc Physics (scientific computing background)
- Certification in Data Science and AI (Boston Institute)

Experience Level: Fresher / Entry Level
"""

SCORER_SYSTEM_PROMPT = """
You are a strict and experienced technical recruiter.
Your job is to evaluate how well a job description matches a candidate profile.

You must respond ONLY with a valid JSON object. No explanation outside the JSON.
No markdown. No code blocks. Just the raw JSON.

JSON format:
{
  "score": <integer 0-100>,
  "verdict": "<STRONG MATCH | GOOD MATCH | WEAK MATCH | NO MATCH>",
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "reasons": ["reason1", "reason2", "reason3"],
  "apply": <true | false>
}

Scoring guide:
  80-100 → STRONG MATCH  (apply immediately)
  60-79  → GOOD MATCH    (worth applying)
  40-59  → WEAK MATCH    (stretch role, apply selectively)
  0-39   → NO MATCH      (skip)

"apply" should be true only if score >= 60.
Be strict. Do not inflate scores.
"""


def score_job(job_description: str) -> dict:
    """
    Takes a job description string.
    Returns a structured scoring result as a dictionary.
    """

    user_prompt = f"""
CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
{job_description}

Score this job for this candidate. Return only the JSON.
"""

    # Call Groq with low temperature for consistent scoring
    raw_response = ask_groq(
        system_prompt=SCORER_SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    # Parse the JSON response
    # The LLM should return clean JSON but we handle edge cases
    result = parse_score_response(raw_response)

    return result


def parse_score_response(raw: str) -> dict:
    """
    Safely parses the LLM's JSON response.
    Handles cases where the LLM adds extra text around the JSON.
    """

    try:
        # First attempt: direct parse
        return json.loads(raw.strip())

    except json.JSONDecodeError:
        # Second attempt: extract JSON block if LLM added extra text
        # Finds the first { and last } and tries to parse that
        match = re.search(r'\{.*\}', raw, re.DOTALL)

        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # If all parsing fails, return a safe fallback
        print(f"⚠️  Could not parse LLM response as JSON.")
        print(f"   Raw response: {raw[:200]}")

        return {
            "score": 0,
            "verdict": "PARSE ERROR",
            "matching_skills": [],
            "missing_skills": [],
            "reasons": ["Could not parse LLM response"],
            "apply": False
        }


def display_score(result: dict, job_title: str = "Unknown Role") -> None:
    """
    Prints the scoring result in a clean readable format.
    """

    # Visual score bar — makes output easy to read at a glance
    filled = int(result['score'] / 5)   # 100 score = 20 blocks
    empty  = 20 - filled
    bar    = "█" * filled + "░" * empty

    verdict_emoji = {
        "STRONG MATCH": "🟢",
        "GOOD MATCH":   "🟡",
        "WEAK MATCH":   "🟠",
        "NO MATCH":     "🔴",
        "PARSE ERROR":  "❌"
    }.get(result['verdict'], "⚪")

    print(f"\n{'='*55}")
    print(f"  JOB: {job_title}")
    print(f"{'='*55}")
    print(f"  SCORE:    {result['score']}/100  [{bar}]")
    print(f"  VERDICT:  {verdict_emoji} {result['verdict']}")
    print(f"  APPLY?    {'✅ YES' if result['apply'] else '❌ NO'}")

    print(f"\n  ✅ MATCHING SKILLS:")
    for skill in result.get('matching_skills', []):
        print(f"     • {skill}")

    print(f"\n  ❌ MISSING SKILLS:")
    for skill in result.get('missing_skills', []):
        print(f"     • {skill}")

    print(f"\n  💭 REASONS:")
    for reason in result.get('reasons', []):
        print(f"     • {reason}")

    print(f"{'='*55}\n")


# ─────────────────────────────────────────────
# TEST — two jobs, one good match, one bad match
# ─────────────────────────────────────────────
if __name__ == "__main__":

    job_1 = {
        "title": "Data Analyst — Remote",
        "description": """
        We are hiring a Data Analyst to join our growing team.
        Requirements:
        - Python and SQL proficiency
        - Experience with Pandas, NumPy, Matplotlib
        - Ability to perform EDA and present insights
        - Knowledge of machine learning basics
        - Familiarity with dashboards and reporting
        - Strong communication skills
        Entry level candidates welcome. GitHub portfolio preferred.
        """
    }

    job_2 = {
        "title": "DevOps Engineer — AWS Infrastructure",
        "description": """
        We need a senior DevOps Engineer with 5+ years experience.
        Requirements:
        - Expert level AWS (EC2, S3, Lambda, EKS)
        - Kubernetes and Docker orchestration
        - Terraform infrastructure as code
        - CI/CD pipeline management (Jenkins, GitHub Actions)
        - Network security and VPC configuration
        - On-site only, Bangalore
        """
    }

    for job in [job_1, job_2]:
        print(f"\nScoring: {job['title']}...")
        result = score_job(job['description'])
        display_score(result, job['title'])