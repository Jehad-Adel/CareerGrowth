"""Loader for extracting raw text from PDF files.

Kept isolated from the `ai.chains` layer so future formats (DOCX, TXT,
OCR) can be added as sibling loaders without touching any chain.
"""

from pathlib import Path

from pypdf import PdfReader


def load_pdf(file_path: str | Path) -> str:
    """Extract and return the concatenated text content of a PDF file.

    Raises:
        FileNotFoundError: if `file_path` does not exist.
        ValueError: if the PDF contains no extractable text.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    reader = PdfReader(path)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise ValueError(f"No extractable text found in PDF: {path}")

    return full_text