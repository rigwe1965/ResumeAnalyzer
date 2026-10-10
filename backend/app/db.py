import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import AnalysisRecord, AnalysisReport, AnalysisSummary, User

DB_PATH = Path(
    os.getenv("DATABASE_PATH", Path(__file__).resolve().parent.parent / "data" / "resume_analyzer.db")
)


class EmailAlreadyRegistered(Exception):
    pass


@contextmanager
def _connect():
    """Commit on success, roll back on error, and always close the connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users (id),
                resume_filename TEXT NOT NULL,
                resume_text TEXT NOT NULL,
                job_description TEXT NOT NULL,
                score INTEGER NOT NULL,
                missing_keywords TEXT NOT NULL,
                skill_gaps TEXT NOT NULL,
                phrasing_suggestions TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        # Databases created before auth existed have no user_id column. Their old rows keep
        # user_id NULL and are not visible to any user.
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(analyses)")}
        if "user_id" not in columns:
            conn.execute("ALTER TABLE analyses ADD COLUMN user_id INTEGER REFERENCES users (id)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analyses (user_id, created_at)"
        )


def create_user(email: str, password_hash: str) -> User:
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        with _connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, password_hash, created_at),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise EmailAlreadyRegistered(email) from exc
    return User(id=user_id, email=email)


def get_user_by_email(email: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> User | None:
    with _connect() as conn:
        row = conn.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(**dict(row)) if row else None


def save_analysis(
    user_id: int, resume_filename: str, resume_text: str, job_description: str, report: AnalysisReport
) -> AnalysisRecord:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses (
                user_id, resume_filename, resume_text, job_description, score,
                missing_keywords, skill_gaps, phrasing_suggestions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                resume_filename,
                resume_text,
                job_description,
                report.score,
                json.dumps(report.missing_keywords),
                json.dumps(report.skill_gaps),
                json.dumps(report.phrasing_suggestions),
                created_at,
            ),
        )
        record_id = cursor.lastrowid

    return AnalysisRecord(
        id=record_id,
        resume_filename=resume_filename,
        created_at=created_at,
        **report.model_dump(),
    )


def list_analyses(user_id: int) -> list[AnalysisSummary]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, resume_filename, score, created_at FROM analyses "
            "WHERE user_id = ? ORDER BY created_at DESC, id DESC",
            (user_id,),
        ).fetchall()
    return [AnalysisSummary(**dict(row)) for row in rows]


def get_analysis(analysis_id: int, user_id: int) -> AnalysisRecord | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?", (analysis_id, user_id)
        ).fetchone()

    if row is None:
        return None

    data = dict(row)
    return AnalysisRecord(
        id=data["id"],
        resume_filename=data["resume_filename"],
        created_at=data["created_at"],
        score=data["score"],
        missing_keywords=json.loads(data["missing_keywords"]),
        skill_gaps=json.loads(data["skill_gaps"]),
        phrasing_suggestions=json.loads(data["phrasing_suggestions"]),
    )
