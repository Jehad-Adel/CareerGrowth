"""Isolated test for the CV Analysis feature.

Loads the sample CV, runs the chain, and prints the structured output.
Not a unit test with assertions — a feature-level smoke test, per the
project's testing convention (load data, call chain, print result).
"""

from pathlib import Path

from app.ai.chains.cv_analysis_chain import build_cv_analysis_chain
from app.ai.loaders.pdf_loader import load_pdf

SAMPLE_CV_PATH = Path(__file__).parent / "sample_data" / "cv.pdf"


def test_cv_analysis() -> None:
    cv_text = load_pdf(SAMPLE_CV_PATH)

    chain = build_cv_analysis_chain()
    result = chain.invoke({"cv_text": cv_text})

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    test_cv_analysis()

# Hits the real Gemini API and costs money. Deselected by default via the
# `-m "not live"` addopts in pyproject.toml; run with `-m live` on purpose.
import pytest  # noqa: E402

pytestmark = pytest.mark.live
