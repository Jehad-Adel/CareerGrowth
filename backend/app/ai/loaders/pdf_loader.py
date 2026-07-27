"""Loader for extracting raw text from PDF files.

Kept isolated from the chains layer so future formats (DOCX, TXT, OCR) can be
added as sibling loaders without touching any chain.
"""

from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

# Uploaded CVs are never written to disk, so the page cap is what bounds the
# work an attacker can make one request do.
DEFAULT_MAX_PAGES = 20


def _extract(reader: PdfReader, max_pages: int, label: str) -> str:
    if len(reader.pages) > max_pages:
        raise ValueError(
            f"That PDF has {len(reader.pages)} pages; the limit is {max_pages}."
        )

    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise ValueError(
            f"No extractable text found in {label}. If it is a scan, it needs OCR."
        )

    return full_text


def load_pdf_bytes(stream: BinaryIO, max_pages: int = DEFAULT_MAX_PAGES) -> str:
    """Extract text from an in-memory PDF.

    This is the upload path: the file never touches the filesystem.

    Raises:
        ValueError: the PDF is unreadable, over the page cap, or has no
            extractable text.
    """
    try:
        reader = PdfReader(stream)
    except Exception as exc:
        raise ValueError("That file is not a readable PDF.") from exc

    return _extract(reader, max_pages, "that PDF")


def load_pdf(file_path: str | Path, max_pages: int = DEFAULT_MAX_PAGES) -> str:
    """Extract text from a PDF on disk. Used by tests and local tooling.

    Raises:
        FileNotFoundError: if `file_path` does not exist.
        ValueError: as `load_pdf_bytes`.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    return _extract(PdfReader(path), max_pages, str(path))
