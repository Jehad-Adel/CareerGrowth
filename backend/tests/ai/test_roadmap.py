"""Isolated test for the Personalized Roadmap feature."""

import pytest

pytestmark = pytest.mark.live

from pathlib import Path

from app.ai.chains.cv_analysis_chain import build_cv_analysis_chain
from app.ai.chains.roadmap_chain import build_roadmap_chain
from app.ai.loaders.pdf_loader import load_pdf

SAMPLE_CV_PATH = Path(__file__).parent / "sample_data" / "cv.pdf"
TARGET_ROLE = "Senior Backend Engineer"


def test_roadmap() -> None:
    cv_text = load_pdf(SAMPLE_CV_PATH)

    cv_profile = build_cv_analysis_chain().invoke({"cv_text": cv_text})

    roadmap_chain = build_roadmap_chain()
    result = roadmap_chain.invoke(
        {
            "cv_profile": cv_profile.model_dump_json(),
            "target_role": TARGET_ROLE,
        }
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_roadmap()