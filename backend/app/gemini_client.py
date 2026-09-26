import json

from fastapi import HTTPException
from google import genai
from google.genai import types

from app.schemas import AnalysisReport

ANALYSIS_PROMPT_TEMPLATE = """You are an expert resume reviewer and technical recruiter.
Compare the resume below against the job description and produce a fitment analysis.

Score the overall fit from 0 to 100, where 100 means the resume is a near-perfect match
for the job description's requirements.

Job description:
---
{job_description}
---

Resume:
---
{resume_text}
---

Return your analysis with:
- missing_keywords: important keywords/skills from the job description that are absent from the resume
- skill_gaps: skills or experience the job requires that the resume doesn't demonstrate
- phrasing_suggestions: concrete suggestions for rewording or restructuring resume content to better match the job
"""


def analyze_resume(client: genai.Client, model: str, resume_text: str, job_description: str) -> AnalysisReport:
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(job_description=job_description, resume_text=resume_text)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalysisReport,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc

    if response.parsed is not None:
        return response.parsed

    try:
        return AnalysisReport.model_validate(json.loads(response.text))
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Gemini returned an unparseable response: {exc}"
        ) from exc
