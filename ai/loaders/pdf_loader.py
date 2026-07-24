"""
==========================================================
CareerFarm AI
PDF Loader
----------------------------------------------------------
Extracts text from PDF files.

Strategy:
1. PyPDF
2. PyMuPDF
3. pdfplumber
==========================================================
"""

from pypdf import PdfReader
import fitz
import pdfplumber


def _extract_with_pypdf(pdf_path: str) -> str:
    text = ""

    try:
        reader = PdfReader(pdf_path)

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    except Exception:
        pass

    return text.strip()


def _extract_with_pymupdf(pdf_path: str) -> str:
    text = ""

    try:
        document = fitz.open(pdf_path)

        for page in document:
            text += page.get_text()

        document.close()

    except Exception:
        pass

    return text.strip()


def _extract_with_pdfplumber(pdf_path: str) -> str:
    text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    except Exception:
        pass

    return text.strip()


def load_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF.

    Strategy:
    1. PyPDF
    2. PyMuPDF
    3. pdfplumber
    """

    text = _extract_with_pypdf(pdf_path)

    if len(text) > 100:
        return text

    text = _extract_with_pymupdf(pdf_path)

    if len(text) > 100:
        return text

    text = _extract_with_pdfplumber(pdf_path)

    return text