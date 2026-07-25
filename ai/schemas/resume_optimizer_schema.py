"""Schema for the AI Resume Optimizer feature."""

from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    """A single section of the optimized resume."""

    title: str = Field(description="Section heading, e.g. 'Professional Summary', 'Experience'.")
    content: list[str] = Field(description="Optimized bullet points or lines for this section.")


class ResumeOptimization(BaseModel):
    """Structured result of optimizing a CV for ATS and, optionally, a target job."""

    ats_score_before: int = Field(
        ge=0, le=100, description="Estimated ATS-friendliness score of the original CV, 0-100."
    )
    ats_score_after: int = Field(
        ge=0, le=100, description="Estimated ATS-friendliness score of the optimized resume, 0-100."
    )
    summary_of_changes: list[str] = Field(
        description="Concise list of the changes made during optimization."
    )
    missing_information: list[str] = Field(
        description="Sections or information absent from the CV that would strengthen it, e.g. "
        "GitHub Portfolio, LinkedIn, Achievements, Metrics, Technical Projects, Certificates."
    )
    optimized_sections: list[ResumeSection] = Field(
        description="The optimized resume broken into sections, e.g. Professional Summary, "
        "Skills, Experience, Projects, Education, Certifications, Languages."
    )
    final_resume_text: str = Field(
        description="The complete optimized resume as clean, professional, ATS-friendly plain text."
    )