"""Schema for the Job Match feature."""

from pydantic import BaseModel, Field, model_validator


class JobMatch(BaseModel):
    """Structured comparison between a candidate's CV and a job description."""

    match_score: int = Field(
        ge=0,
        le=100,
        description="Overall match score between the CV and the job description, from 0 to 100.",
    )
    matched_skills: list[str] = Field(
        description="Skills required by the job that are explicitly present in the CV."
    )
    missing_skills: list[str] = Field(
        description="Skills required by the job that are not present in the CV."
    )
    strengths: list[str] = Field(
        description="Aspects of the CV that make the candidate a strong fit for this job."
    )
    weaknesses: list[str] = Field(
        description="Aspects of the CV that weaken the candidate's fit for this job."
    )
    recommendations: list[str] = Field(
        description="Actionable recommendations to close the gap, derived from missing_skills."
    )
    summary: str = Field(
        description="A concise 2-4 sentence summary of the overall match."
    )

    @model_validator(mode="after")
    def _dedupe_and_resolve_overlap(self) -> "JobMatch":
        """Dedupe both skill lists and drop any skill claimed as both matched and missing."""

        def dedupe(items: list[str]) -> list[str]:
            seen: set[str] = set()
            result: list[str] = []
            for item in items:
                key = item.strip().lower()
                if key and key not in seen:
                    seen.add(key)
                    result.append(item.strip())
            return result

        matched = dedupe(self.matched_skills)
        matched_keys = {skill.lower() for skill in matched}
        missing = [
            skill for skill in dedupe(self.missing_skills) if skill.lower() not in matched_keys
        ]

        self.matched_skills = matched
        self.missing_skills = missing
        return self