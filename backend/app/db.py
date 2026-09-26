import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.schemas import AnalysisRecord, AnalysisReport, AnalysisSummary

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "resume_analyzer.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def save_analysis(resume_filename: str, resume_text: str, job_description: str, report: AnalysisReport) -> AnalysisRecord:
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analyses (
                resume_filename, resume_text, job_description, score,
                missing_keywords, skill_gaps, phrasing_suggestions, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
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


def list_analyses() -> list[AnalysisSummary]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, resume_filename, score, created_at FROM analyses ORDER BY created_at DESC"
        ).fetchall()
    return [AnalysisSummary(**dict(row)) for row in rows]


def get_analysis(analysis_id: int) -> AnalysisRecord | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()

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
