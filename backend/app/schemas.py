from pydantic import BaseModel, Field


class AnalysisReport(BaseModel):
    """Structured fitment report returned by Gemini."""

    score: int = Field(ge=0, le=100, description="Overall fitment score, 0-100")
    missing_keywords: list[str] = Field(
        description="Important keywords/skills from the job description absent from the resume"
    )
    skill_gaps: list[str] = Field(
        description="Skills or experience the job requires that the resume doesn't demonstrate"
    )
    phrasing_suggestions: list[str] = Field(
        description="Concrete suggestions for rewording or restructuring resume content"
    )


class AnalysisRecord(AnalysisReport):
    """A persisted analysis run, including its identifying/history fields."""

    id: int
    resume_filename: str
    created_at: str


class User(BaseModel):
    id: int
    email: str


class Credentials(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class AnalysisSummary(BaseModel):
    """Lightweight row for the history list view."""

    id: int
    resume_filename: str
    score: int
    created_at: str
