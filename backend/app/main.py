import os

from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from app import db
from app.gemini_client import analyze_resume
from app.resume_parser import extract_resume_text
from app.schemas import AnalysisRecord, AnalysisSummary

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

app = FastAPI(title="Resume Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


def _get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    return genai.Client(api_key=GEMINI_API_KEY)


@app.get("/api/ping-gemini")
def ping_gemini():
    client = _get_gemini_client()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Say hello in one short sentence and confirm you are reachable.",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    return {"response": response.text}


@app.post("/api/analyze", response_model=AnalysisRecord)
async def analyze(resume: UploadFile, job_description: str = Form(...)):
    job_description = job_description.strip()
    if not job_description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    content = await resume.read()
    resume_text = extract_resume_text(resume.filename, content)

    client = _get_gemini_client()
    report = analyze_resume(client, GEMINI_MODEL, resume_text, job_description)

    return db.save_analysis(
        resume_filename=resume.filename,
        resume_text=resume_text,
        job_description=job_description,
        report=report,
    )


@app.get("/api/analyses", response_model=list[AnalysisSummary])
def get_analyses():
    return db.list_analyses()


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisRecord)
def get_analysis(analysis_id: int):
    record = db.get_analysis(analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return record
