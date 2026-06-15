# ──────────────────────────────────────────────────────────────
# PURPOSE: Generate a tailored cover letter by combining
#          the job description + retrieved resume context
#
# This is the final output the user sees and uses directly
# ──────────────────────────────────────────────────────────────

import sys
import os

# Add parent directory to path so we can import resume_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from writer.groq_client import ask_groq
from resume_engine.retrieve import get_relevant_chunks, format_chunks_for_llm

WRITER_SYSTEM_PROMPT = """
You are an expert cover letter writer for tech and data science roles.

Your rules:
1. Write in first person as the candidate
2. ONLY use experience and skills from the provided resume context
3. NEVER invent or exaggerate qualifications
4. Be specific — mention actual project names and technologies
5. Keep it to exactly 3 paragraphs:
   Paragraph 1: Why this role excites you + your strongest match
   Paragraph 2: 2 specific projects that prove your skills
   Paragraph 3: Forward-looking close with enthusiasm
6. Professional but warm tone — not robotic
7. No "Dear Sir/Madam" — use "Dear Hiring Team" if company unknown
8. Length: 200-250 words maximum
9. Do not include subject line or signature — just the letter body
"""


def generate_cover_letter(
    job_description: str,
    company_name: str = "the company",
    job_title: str = "this role"
) -> dict:
    """
    Full pipeline:
    1. Retrieve relevant resume chunks for this job
    2. Format them for the LLM
    3. Generate cover letter using Groq
    4. Return everything as a structured result
    """

    # Step 1: Retrieve the most relevant resume sections
    # This is Milestone 1 doing its job inside Milestone 3
    print("  → Retrieving relevant resume sections...")
    chunks = get_relevant_chunks(job_description, top_k=3)
    resume_context = format_chunks_for_llm(chunks)

    # Step 2: Show which sections were retrieved
    print(f"  → Using sections: {[c['section'] for c in chunks]}")

    # Step 3: Build the prompt
    user_prompt = f"""
COMPANY: {company_name}
ROLE: {job_title}

JOB DESCRIPTION:
{job_description}

CANDIDATE'S RELEVANT RESUME SECTIONS:
{resume_context}

Write a tailored cover letter for this candidate applying to this role.
Only use the experience shown in the resume sections above.
"""

    # Step 4: Generate the cover letter
    print("  → Generating cover letter with Groq...")
    cover_letter = ask_groq(
        system_prompt=WRITER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        # Slightly higher temperature for more natural writing
        # than the scorer — we want it to sound human, not robotic
    )

    # Step 5: Package the full result
    return {
        "company":       company_name,
        "job_title":     job_title,
        "cover_letter":  cover_letter,
        "used_sections": [c['section'] for c in chunks],
        "distances":     [c['distance'] for c in chunks]
    }


def display_cover_letter(result: dict) -> None:
    """
    Prints the cover letter result cleanly.
    """
    print(f"\n{'='*60}")
    print(f"  COVER LETTER — {result['job_title']} at {result['company']}")
    print(f"{'='*60}")
    print(f"\n  Resume sections used: {result['used_sections']}")
    print(f"  Relevance distances:  {result['distances']}")
    print(f"\n{'-'*60}\n")
    print(result['cover_letter'])
    print(f"\n{'-'*60}")
    word_count = len(result['cover_letter'].split())
    print(f"  Word count: {word_count}")
    print(f"{'='*60}\n")


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    test_job = {
        "description": """
        We are hiring a Junior Data Analyst to join our analytics team.
        You will work with Python and SQL to clean, analyze and visualize 
        data. Experience with machine learning is a plus.
        We value candidates who have built real projects and can explain
        their work clearly. Remote friendly. Entry level welcome.
        GitHub portfolio is a strong plus.
        """,
        "company": "DataWorks Analytics",
        "title": "Junior Data Analyst"
    }

    print(f"\nGenerating cover letter for: {test_job['title']}")
    print(f"Company: {test_job['company']}\n")

    result = generate_cover_letter(
        job_description=test_job['description'],
        company_name=test_job['company'],
        job_title=test_job['title']
    )

    display_cover_letter(result)