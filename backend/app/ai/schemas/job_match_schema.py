"""Schema for the Job Match feature."""

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

RequirementLevel = Literal["Required", "Preferred"]
GapSeverity = Literal["Blocking", "Significant", "Minor"]

# What an unmatched skill costs the candidate when the model omits the call.
# "Significant" rather than "Blocking": inventing the harshest verdict from
# missing data would misinform, and "Minor" would hide a real gap.
_DEFAULT_SEVERITY: GapSeverity = "Significant"


class SkillMatch(BaseModel):
    """One job requirement, judged against the CV.

    Replaces the old pair of flat string lists. A recruiter's real question is
    not "is this skill present" but "how badly does its absence hurt", and a
    partial credit case — Django experience against a Flask requirement —
    could previously only be recorded as a lie in one direction or the other.
    """

    job_skill: str = Field(
        description="The skill exactly as named or implied in the job description."
    )
    requirement_level: RequirementLevel = Field(
        description=(
            "Required if the job description marks this as mandatory (e.g. 'must "
            "have', 'required', listed under core requirements). Preferred if "
            "marked as a bonus (e.g. 'nice to have', 'a plus'). Default to "
            "Required when unmarked."
        )
    )
    matched: bool = Field(
        description="True if the CV demonstrates this skill, directly or transferably."
    )
    matched_via: str | None = Field(
        default=None,
        description=(
            "If matched, the specific CV skill or experience that satisfies this "
            "requirement. Null if not matched."
        ),
    )
    is_transferable_match: bool = Field(
        default=False,
        description=(
            "True if matched through a closely related but not identical skill "
            "(e.g. Django experience satisfying a Flask requirement) rather than "
            "an exact or near-exact name match. False otherwise."
        ),
    )
    severity_if_missing: GapSeverity | None = Field(
        default=None,
        description=(
            "How much this gap hurts candidacy: Blocking (a Required skill central "
            "to the role with no transferable overlap), Significant (a Required "
            "skill with partial overlap, or a heavily emphasized Preferred skill), "
            "Minor (a lightly emphasized Preferred skill). Null when matched."
        ),
    )


class JobMatch(BaseModel):
    """Structured comparison between a candidate's CV and a job description."""

    match_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Overall skill-coverage score from 0 to 100, weighted by "
            "requirement_level and consistent with skill_matches."
        ),
    )
    hiring_probability: int = Field(
        default=0,
        ge=0,
        le=100,
        description=(
            "Holistic estimate of this candidate passing an initial resume screen "
            "for this exact role, accounting for seniority fit, required-skill "
            "coverage, and transferable strengths. Not simply match_score."
        ),
    )
    hiring_probability_reasoning: str = Field(
        default="",
        description="A 1-2 sentence justification for hiring_probability.",
    )
    skill_matches: list[SkillMatch] = Field(
        default_factory=list,
        description="Every skill identified in the job description, compared against the CV.",
    )
    strengths: list[str] = Field(
        description="Aspects of the CV that make the candidate a strong fit for this job."
    )
    weaknesses: list[str] = Field(
        description="Aspects of the CV that weaken the candidate's fit for this job."
    )
    recommendations: list[str] = Field(
        description="Actionable recommendations to close the gap, derived from unmatched skills."
    )
    summary: str = Field(
        description="A concise 2-4 sentence summary of the overall match."
    )

    @model_validator(mode="after")
    def _clean_skill_matches(self) -> "JobMatch":
        """Dedupe by skill name and force the conditional fields to agree.

        The model routinely returns a `severity_if_missing` alongside
        `matched: true`, or a `matched_via` on a skill it just called absent.
        Left alone, both render as contradictions in the UI.
        """
        seen: set[str] = set()
        deduped: list[SkillMatch] = []
        for item in self.skill_matches:
            key = item.job_skill.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            item.job_skill = item.job_skill.strip()

            if item.matched:
                item.severity_if_missing = None
            else:
                item.matched_via = None
                item.is_transferable_match = False
                item.severity_if_missing = item.severity_if_missing or _DEFAULT_SEVERITY

            deduped.append(item)

        self.skill_matches = deduped
        return self

    # The two flat lists the first version of this schema returned. Kept as
    # computed fields, not dropped: they serialize into the stored `result`
    # JSON, so existing readers — the skill seeder, the jobs page, anything
    # reading an older row — keep working while new code uses skill_matches.
    @computed_field  # type: ignore[prop-decorator]
    @property
    def matched_skills(self) -> list[str]:
        """Job skills the CV evidences, directly or transferably."""
        return [item.job_skill for item in self.skill_matches if item.matched]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def missing_skills(self) -> list[str]:
        """Job skills the CV does not evidence."""
        return [item.job_skill for item in self.skill_matches if not item.matched]

    @property
    def blocking_gaps(self) -> list[SkillMatch]:
        """Unmatched Required skills with no transferable overlap."""
        return [
            item
            for item in self.skill_matches
            if not item.matched and item.severity_if_missing == "Blocking"
        ]
