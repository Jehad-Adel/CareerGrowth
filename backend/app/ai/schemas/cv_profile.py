"""Schema for the CV Analysis feature."""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SeniorityLevel(str, Enum):
    """Career seniority tiers used across CV Analysis and Job Matching."""

    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"


class EmploymentPeriod(BaseModel):
    """A single dated role extracted from the CV.

    Captured separately from `years_of_experience` so the chain can total the
    experience from real dates. Asking the LLM to add up date ranges itself is
    the unreliable part; asking it to copy the dates down is not.
    """

    title: str | None = Field(
        default=None, description="Job title held during this period, if stated."
    )
    company: str | None = Field(
        default=None, description="Employer name during this period, if stated."
    )
    start_date: str | None = Field(
        default=None,
        description=(
            "Start date normalized to 'YYYY-MM', or 'YYYY' if only the year is "
            "stated. Null if not explicitly stated."
        ),
    )
    end_date: str | None = Field(
        default=None,
        description=(
            "End date in the same format as start_date. Null if the role is "
            "current (see is_current) or the end date is not explicitly stated."
        ),
    )
    is_current: bool = Field(
        default=False,
        description=(
            "True if the CV explicitly marks this role as ongoing "
            "(e.g. 'Present', 'Current')."
        ),
    )


class CVProfile(BaseModel):
    """Structured representation of a candidate extracted from their CV.

    Field descriptions double as the extraction instructions passed to
    the LLM through `with_structured_output`, so they must be precise.
    """

    full_name: str | None = Field(
        default=None,
        description="Candidate's full name as it appears on the CV, if present.",
    )
    current_role: str | None = Field(
        default=None,
        description="The candidate's most recent or current job title.",
    )
    years_of_experience: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Total professional experience in years. Only a fallback signal — the "
            "chain recomputes the authoritative value from employment_periods, so "
            "spend the effort on accurate dates there. Null if the CV does not "
            "provide enough explicit dates to compute this without guessing."
        ),
    )
    employment_periods: list[EmploymentPeriod] = Field(
        default_factory=list,
        description=(
            "Every explicitly dated role found in the CV, used to compute "
            "years_of_experience deterministically. Empty list if the CV has no "
            "dated roles."
        ),
    )
    seniority_level: SeniorityLevel = Field(
        description=(
            "Overall seniority based only on explicitly stated job titles, the "
            "computed years_of_experience, and the scope of responsibility the CV "
            "describes. Never guessed from unstated context."
        )
    )
    skills: list[str] = Field(
        description="Technical and professional skills explicitly demonstrated in the CV."
    )
    strengths: list[str] = Field(
        description="Notable strengths of the candidate based on their experience and achievements."
    )
    weaknesses: list[str] = Field(
        description="Gaps, inconsistencies, or areas that weaken the CV's overall impact."
    )
    summary: str = Field(
        description="A concise 2-4 sentence professional summary of the candidate."
    )
    improvement_suggestions: list[str] = Field(
        description="Concrete, actionable suggestions to improve the CV's content or presentation."
    )
    extraction_confidence: int = Field(
        default=100,
        ge=0,
        le=100,
        description=(
            "Confidence that this extraction is accurate and complete, judged from "
            "the clarity, structure, and completeness of the CV text. Lower it for "
            "garbled text, missing dates, or ambiguous sections."
        ),
    )

    @model_validator(mode="after")
    def _clean_extracted_lists(self) -> "CVProfile":
        """Dedupe every list field and drop skills that are extraction debris."""
        self.skills = _dedupe_and_filter_skills(self.skills)
        self.strengths = _dedupe(self.strengths)
        self.weaknesses = _dedupe(self.weaknesses)
        self.improvement_suggestions = _dedupe(self.improvement_suggestions)
        return self


# Characters that appear inside real skill names and must not count against a
# token: C++, C#, .NET, CI/CD, Node.js, Objective-C.
_SKILL_PUNCTUATION = set("+#.-/ ")

# Above this share of characters that are neither alphanumeric nor ordinary
# skill punctuation, a token is extraction debris rather than a skill.
_MAX_NOISE_RATIO = 0.3


def _looks_like_extraction_debris(token: str) -> bool:
    """Heuristic for PDF/OCR artifacts that the model listed as a skill.

    Deliberately does *not* reject every one-character token: `C` and `R` are
    both real languages, and dropping them would be a worse error than keeping
    a stray bullet glyph. A single character is rejected only when it is not a
    letter or digit.
    """
    if not token:
        return True
    if len(token) == 1:
        return not token.isalnum()
    if not any(char.isalpha() or char.isdigit() for char in token):
        return True
    noisy = sum(
        1
        for char in token
        if not (char.isalnum() or char in _SKILL_PUNCTUATION)
    )
    return (noisy / len(token)) > _MAX_NOISE_RATIO


def _dedupe(items: list[str]) -> list[str]:
    """Case-insensitive dedupe, preserving first occurrence and order."""
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        cleaned = item.strip()
        key = cleaned.lower()
        if key and key not in seen:
            seen.add(key)
            deduped.append(cleaned)
    return deduped


def _dedupe_and_filter_skills(skills: list[str]) -> list[str]:
    """Dedupe skills and drop the ones that are extraction debris."""
    return [
        skill for skill in _dedupe(skills) if not _looks_like_extraction_debris(skill)
    ]
