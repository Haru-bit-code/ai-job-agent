# ──────────────────────────────────────────────────────────────
# PURPOSE: Single entry point for the entire project
# Always run from project root: python run.py
# This ensures Python path is always correct
# ──────────────────────────────────────────────────────────────

import sys
import os
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

# Add project root to Python path permanently
# This line makes ALL imports work correctly from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can safely import from any module
from writer.cover_letter import generate_cover_letter, display_cover_letter

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