# ──────────────────────────────────────────────────────────────
# PURPOSE: Database setup and table definitions
# SQLite stores all job applications, scores, cover letters
# Think of this as your filing cabinet
# ──────────────────────────────────────────────────────────────

import sqlite3
import os
from datetime import datetime

DB_PATH = "data/applications.db"


def get_connection():
    """
    Returns a database connection.
    check_same_thread=False needed for FastAPI's async nature.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # row_factory makes rows behave like dictionaries
    # so you can do row["score"] instead of row[3]
    return conn


def init_db():
    """
    Creates the applications table if it doesn't exist.
    Safe to call multiple times — won't overwrite existing data.
    """
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title       TEXT NOT NULL,
            company         TEXT NOT NULL,
            job_description TEXT NOT NULL,
            score           INTEGER,
            verdict         TEXT,
            matching_skills TEXT,
            missing_skills  TEXT,
            cover_letter    TEXT,
            apply           BOOLEAN,
            status          TEXT DEFAULT 'pending',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # status tracks: pending → applied → interview → rejected → offer

    conn.commit()
    conn.close()
    print("✅ Database initialized at:", DB_PATH)


def save_application(data: dict) -> int:
    """
    Saves a complete job application to the database.
    Returns the new record's ID.
    """
    import json

    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO applications 
        (job_title, company, job_description, score, verdict,
         matching_skills, missing_skills, cover_letter, apply)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("job_title", "Unknown"),
        data.get("company", "Unknown"),
        data.get("job_description", ""),
        data.get("score", 0),
        data.get("verdict", ""),
        json.dumps(data.get("matching_skills", [])),
        json.dumps(data.get("missing_skills", [])),
        data.get("cover_letter", ""),
        data.get("apply", False)
    ))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_all_applications() -> list[dict]:
    """
    Returns all saved applications, newest first.
    """
    import json

    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM applications 
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()

    applications = []
    for row in rows:
        app = dict(row)
        # Parse JSON strings back to lists
        app["matching_skills"] = json.loads(app["matching_skills"] or "[]")
        app["missing_skills"]  = json.loads(app["missing_skills"] or "[]")
        applications.append(app)

    return applications


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("Database ready.")