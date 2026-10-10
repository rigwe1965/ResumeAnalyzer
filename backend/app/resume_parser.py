import logging
from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader

logger = logging.getLogger(__name__)

MAX_RESUME_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PDF_PAGES = 20
MAX_RESUME_CHARS = 50_000
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
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Markdown resume must be UTF-8 encoded text.")
    else:
        if not content.lstrip().startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="That file isn't a valid PDF.")
        try:
            reader = PdfReader(BytesIO(content))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise HTTPException(
                    status_code=413, detail=f"Resume PDF has too many pages (max {MAX_PDF_PAGES})."
                )
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except HTTPException:
            raise
        except Exception:
            logger.exception("Could not read PDF")
            raise HTTPException(status_code=400, detail="Could not read that PDF.")

    text = text.strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the resume. Scanned/image-only PDFs aren't supported.",
        )

    if len(text) > MAX_RESUME_CHARS:
        raise HTTPException(status_code=413, detail="Resume text is too long.")

    return text
