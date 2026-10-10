import pytest
from fastapi import HTTPException

from app.resume_parser import MAX_RESUME_BYTES, extract_resume_text


def test_markdown_is_decoded():
    assert extract_resume_text("cv.md", b"# Jane\nPython") == "# Jane\nPython"


def test_markdown_with_bom_is_decoded():
    assert extract_resume_text("cv.md", b"\xef\xbb\xbfHello") == "Hello"


@pytest.mark.parametrize("filename", [None, "", "cv.docx", "cv.txt", "cv"])
def test_unsupported_extension_rejected(filename):
    with pytest.raises(HTTPException) as exc:
        extract_resume_text(filename, b"hello")
    assert exc.value.status_code == 400


def test_oversized_file_rejected():
    with pytest.raises(HTTPException) as exc:
        extract_resume_text("cv.md", b"a" * (MAX_RESUME_BYTES + 1))
    assert exc.value.status_code == 413


def test_non_utf8_markdown_rejected():
    with pytest.raises(HTTPException) as exc:
        extract_resume_text("cv.md", b"\xff\xfe\x00bad")
    assert exc.value.status_code == 400


def test_fake_pdf_rejected():
    with pytest.raises(HTTPException) as exc:
        extract_resume_text("cv.pdf", b"not a pdf")
    assert exc.value.status_code == 400


def test_empty_markdown_rejected():
    with pytest.raises(HTTPException) as exc:
        extract_resume_text("cv.md", b"   \n ")
    assert exc.value.status_code == 400
