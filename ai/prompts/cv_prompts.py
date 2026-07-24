from langchain_core.prompts import PromptTemplate

from ai.parsers.cv_parser import cv_parser


cv_prompt = PromptTemplate(
    template="""
You are an expert ATS Resume Analyzer.

Analyze the resume carefully.

Extract ONLY information that exists in the resume.

If information is missing return an empty list.

Return ONLY valid JSON.

Fields:

- name
- education
- skills
- projects
- experience
- certificates
- soft_skills
- strengths
- weaknesses
- missing_skills
- ats_score
- summary

Do not write markdown.
Do not explain.
Return JSON only.

Resume:

{cv}

{format_instructions}
""",
    input_variables=["cv"],
    partial_variables={
        "format_instructions": cv_parser.get_format_instructions()
    }
)