"""Loader for extracting raw text from PDF files.

Kept isolated from the chains layer so future formats (DOCX, TXT, OCR) can be
added as sibling loaders without touching any chain.
"""

import re
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

# Uploaded CVs are never written to disk, so the page cap is what bounds the
# work an attacker can make one request do.
DEFAULT_MAX_PAGES = 20

# Non-printable bytes that survive extraction from a badly generated PDF. They
# carry no meaning and cost tokens.
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Dot leaders and rule lines ("Experience.........", "-------"). Three or more
# of the same punctuation mark, collapsed to one. The three-repeat floor is
# what keeps "C++" and "--flag" intact.
_REPEATED_PUNCTUATION = re.compile(r"([^\w\s])\1{2,}")
_REPEATED_SPACING = re.compile(r"[ \t]{2,}")
_REPEATED_BLANK_LINES = re.compile(r"\n{3,}")


def clean_extracted_text(text: str) -> str:
    """Strip extraction artifacts without touching real content.

    Two-column CVs and table-based templates come out of pypdf padded with
    long runs of spaces, dot leaders, and blank lines. That noise reaches the
    model as tokens, and the model reads some of it back as skills, which is
    what the schema's debris filter then has to undo.

    Formatting only: no word is altered, dropped, or reordered.
    """
    text = _CONTROL_CHARS.sub("", text)
    text = _REPEATED_PUNCTUATION.sub(r"\1", text)
    text = _REPEATED_SPACING.sub(" ", text)
    # Strip per line before collapsing blank runs, so a line of pure padding
    # becomes empty and is then collapsed rather than surviving as a "blank".
    text = "\n".join(line.strip() for line in text.splitlines())
    return _REPEATED_BLANK_LINES.sub("\n\n", text).strip()


def _extract(reader: PdfReader, max_pages: int, label: str) -> str:
    if len(reader.pages) > max_pages:
        raise ValueError(
            f"That PDF has {len(reader.pages)} pages; the limit is {max_pages}."
        )

    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = clean_extracted_text("\n".join(pages_text))

    # Checked after cleaning: a PDF whose only "text" is control characters is
    # as unreadable as an empty one, and must fail the same way.
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
