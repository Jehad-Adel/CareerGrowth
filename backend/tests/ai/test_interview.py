"""Isolated test for the Interview Simulator feature."""

import pytest

pytestmark = pytest.mark.live

from pathlib import Path

from app.ai.chains.interview_chain import build_interview_chain
from app.ai.loaders.pdf_loader import load_pdf
from app.ai.schemas.interview_schema import ConversationTurn, InterviewLevel

SAMPLE_CV_PATH = Path(__file__).parent / "sample_data" / "cv.pdf"
SAMPLE_JOB_PATH = Path(__file__).parent / "sample_data" / "job.txt"


def test_interview() -> None:
    cv_text = load_pdf(SAMPLE_CV_PATH)
    job_description = SAMPLE_JOB_PATH.read_text()
    chain = build_interview_chain()

    first_turn = chain.invoke(
        {
            "cv_text": cv_text,
            "job_description": job_description,
            "interview_level": InterviewLevel.TECHNICAL_LEAD,
            "conversation_history": [],
        }
    )
    print(first_turn.model_dump_json(indent=2))

    conversation_history = [
        ConversationTurn(
            question=first_turn.current_question,
            answer="I used FastAPI because it's fast and has automatic docs.",
        )
    ]

    second_turn = chain.invoke(
        {
            "cv_text": cv_text,
            "job_description": job_description,
            "interview_level": InterviewLevel.TECHNICAL_LEAD,
            "conversation_history": conversation_history,
            "interviewer_name": first_turn.interviewer_name,
        }
    )
    assert second_turn.interviewer_name == first_turn.interviewer_name
    print(second_turn.model_dump_json(indent=2))


if __name__ == "__main__":
    test_interview()