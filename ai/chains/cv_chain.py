"""
==========================================================
CareerFarm AI
CV Analysis Chain
----------------------------------------------------------
Responsible for:
    • Receiving extracted CV text.
    • Sending it to Gemini.
    • Parsing the structured output.
==========================================================
"""

from ai.llm.llm import get_llm
from ai.prompts.cv_prompts import cv_prompt
from ai.parsers.cv_parser import cv_parser


def analyze_cv(cv_text: str):
    """
    Analyze a resume and return a structured CVProfile object.
    """

    llm = get_llm()

    prompt = cv_prompt.format(
        cv=cv_text,
    )

    response = llm.generate_content(prompt)

    result = cv_parser.parse(response.text)

    return result