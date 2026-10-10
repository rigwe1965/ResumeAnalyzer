import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from app import auth, db
from app.gemini_client import analyze_resume, build_client
from app.rate_limit import limit_by_ip, limit_by_user
from app.resume_parser import MAX_RESUME_BYTES, extract_resume_text
from app.schemas import AnalysisRecord, AnalysisSummary, Credentials, TokenResponse, User

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
MAX_JOB_DESCRIPTION_CHARS = 20_000

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    auth.get_jwt_secret()  # fail fast if JWT_SECRET is missing/weak
    db.init_db()
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set; analysis endpoints will fail until it is.")
    yield


app = FastAPI(title="Resume Analyzer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    return build_client(GEMINI_API_KEY)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post(
    "/api/auth/register",
    response_model=TokenResponse,
    status_code=201,
    dependencies=[Depends(limit_by_ip("register", limit=5, window_seconds=3600))],
)
def register(credentials: Credentials):
    email = auth.normalize_email(credentials.email)
    auth.validate_password(credentials.password)
    try:
        user = db.create_user(email, auth.hash_password(credentials.password))
    except db.EmailAlreadyRegistered:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    return TokenResponse(access_token=auth.create_access_token(user), user=user)


@app.post(
    "/api/auth/login",
    response_model=TokenResponse,
    dependencies=[Depends(limit_by_ip("login", limit=10, window_seconds=900))],
)
def login(credentials: Credentials):
    user = auth.authenticate(credentials.email, credentials.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return TokenResponse(access_token=auth.create_access_token(user), user=user)


@app.get("/api/auth/me", response_model=User)
def me(user: User = Depends(limit_by_user("me", limit=120, window_seconds=60))):
    return user


@app.get("/api/ping-gemini")
def ping_gemini(_: User = Depends(limit_by_user("ping", limit=5, window_seconds=3600))):
    client = _get_gemini_client()
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Say hello in one short sentence and confirm you are reachable.",
        )
    except Exception:
        logger.exception("Gemini ping failed")
        raise HTTPException(status_code=502, detail="Gemini request failed.")

    return {"response": response.text}


@app.post("/api/analyze", response_model=AnalysisRecord)
def analyze(
    resume: UploadFile,
    job_description: str = Form(...),
    user: User = Depends(limit_by_user("analyze", limit=10, window_seconds=3600)),
):
    # Plain `def`: FastAPI runs it in a threadpool, so the blocking Gemini/SQLite calls
    # don't stall the event loop.
    job_description = job_description.strip()
    if not job_description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    if len(job_description) > MAX_JOB_DESCRIPTION_CHARS:
        raise HTTPException(status_code=413, detail="Job description is too long.")

    content = resume.file.read(MAX_RESUME_BYTES + 1)
    resume_text = extract_resume_text(resume.filename, content)

    client = _get_gemini_client()
    report = analyze_resume(client, GEMINI_MODEL, resume_text, job_description)

    return db.save_analysis(
        user_id=user.id,
        resume_filename=resume.filename,
        resume_text=resume_text,
        job_description=job_description,
        report=report,
    )


@app.get("/api/analyses", response_model=list[AnalysisSummary])
def get_analyses(user: User = Depends(limit_by_user("read", limit=120, window_seconds=60))):
    return db.list_analyses(user.id)


@app.get("/api/analyses/{analysis_id}", response_model=AnalysisRecord)
def get_analysis(
    analysis_id: int, user: User = Depends(limit_by_user("read", limit=120, window_seconds=60))
):
    record = db.get_analysis(analysis_id, user.id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return record
