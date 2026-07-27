"""Isolated test for the Job Match feature."""

import pytest

pytestmark = pytest.mark.live

from pathlib import Path

from app.ai.chains.job_match_chain import build_job_match_chain
from app.ai.loaders.pdf_loader import load_pdf

SAMPLE_CV_PATH = Path(__file__).parent / "sample_data" / "cv.pdf"
SAMPLE_JOB_PATH = Path(__file__).parent / "sample_data" / "job.txt"


def test_job_match() -> None:
    cv_text = load_pdf(SAMPLE_CV_PATH)
    job_description = SAMPLE_JOB_PATH.read_text()

    chain = build_job_match_chain()
    result = chain.invoke({"cv_text": cv_text, "job_description": job_description})

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_job_match()