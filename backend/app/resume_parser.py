from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader

MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB
SUPPORTED_EXTENSIONS = (".pdf", ".md")


def extract_resume_text(filename: str | None, content: bytes) -> str:
    if not filename or not filename.lower().endswith(SUPPORTED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload a .pdf or .md resume.",
        )

    if len(content) > MAX_RESUME_BYTES:
        raise HTTPException(status_code=413, detail="Resume file is too large (max 5MB).")

    if filename.lower().endswith(".md"):
        text = content.decode("utf-8", errors="ignore")
    else:
        try:
            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not read PDF: {exc}") from exc

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text could be extracted from the resume.")

    return text
