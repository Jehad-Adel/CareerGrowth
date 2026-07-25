"""Isolated test for the AI Resume Optimizer feature."""

from pathlib import Path

from ai.chains.resume_optimizer_chain import build_resume_optimizer_chain
from ai.loaders.pdf_loader import load_pdf

SAMPLE_CV_PATH = Path(__file__).parent / "sample_data" / "cv.pdf"
SAMPLE_JOB_PATH = Path(__file__).parent / "sample_data" / "job.txt"


def test_resume_optimizer() -> None:
    cv_text = load_pdf(SAMPLE_CV_PATH)
    job_description = SAMPLE_JOB_PATH.read_text()
    chain = build_resume_optimizer_chain()

    targeted_result = chain.invoke({"cv_text": cv_text, "job_description": job_description})
    print(targeted_result.model_dump_json(indent=2))

    general_result = chain.invoke({"cv_text": cv_text, "job_description": None})
    print(general_result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_resume_optimizer()