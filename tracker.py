import sqlite3
from datetime import datetime

DB_PATH = "jobs.db"


def init_db():
    """Create the SQLite DB and seen_jobs table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id   TEXT PRIMARY KEY,
            title    TEXT,
            company  TEXT,
            seen_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_seen(job_id: str) -> bool:
    """Return True if the job_id has already been recorded."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT 1 FROM seen_jobs WHERE job_id = ?", (job_id,)
    ).fetchone()
    conn.close()
    return row is not None


def mark_seen(job_id: str, title: str, company: str):
    """Insert a new job record into the seen_jobs table."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen_jobs (job_id, title, company, seen_at) VALUES (?, ?, ?, ?)",
        (job_id, title, company, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_seen_count() -> int:
    """Return the total number of jobs tracked so far."""
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM seen_jobs").fetchone()[0]
    conn.close()
    return count


def get_recent_jobs(limit: int = 5) -> list[dict]:
    """Return the most recently seen jobs."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT job_id, title, company, seen_at FROM seen_jobs ORDER BY seen_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [{"job_id": r[0], "title": r[1], "company": r[2], "seen_at": r[3]} for r in rows]
