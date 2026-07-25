"""Isolated test for the Skill Gap Analyzer feature."""

from pathlib import Path

from ai.chains.skill_gap_chain import build_skill_gap_chain
from ai.loaders.pdf_loader import load_pdf

SAMPLE_CV_PATH = Path(__file__).parent / "sample_data" / "cv.pdf"
SAMPLE_JOB_PATH = Path(__file__).parent / "sample_data" / "job.txt"


def test_skill_gap() -> None:
    cv_text = load_pdf(SAMPLE_CV_PATH)
    job_description = SAMPLE_JOB_PATH.read_text()

    chain = build_skill_gap_chain()
    result = chain.invoke({"cv_text": cv_text, "job_description": job_description})

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_skill_gap()