from pydantic import BaseModel, Field


class CompensationAnalysis(BaseModel):
    base_salary_range: str = Field(
        description="Estimated market range for base salary, e.g. '$120k-$150k'."
    )
    equity_range: str = Field(
        default="",
        description="Estimated equity range if applicable, e.g. '0.1%-0.3%'.",
    )
    bonus_range: str = Field(
        default="",
        description="Expected bonus range, e.g. '10%-20%'.",
    )
    total_comp_range: str = Field(
        description="Estimated total compensation range."
    )
    market_percentile: str = Field(
        description="Where this offer falls in the market, e.g. '75th percentile'."
    )


class GrowthPotential(BaseModel):
    promotion_track: str = Field(
        description="Assessment of promotion opportunities and career growth."
    )
    skill_development: str = Field(
        description="Opportunities for learning and skill development."
    )
    mentorship: str = Field(
        description="Mentorship and guidance available at this company."
    )


class WorkLifeBalance(BaseModel):
    remote_policy: str = Field(description="Remote/hybrid/onsite policy.")
    hours_expectation: str = Field(
        description="Expected working hours and intensity."
    )
    travel_requirement: str = Field(
        default="",
        description="Any travel requirements for the role."
    )


class OfferScore(BaseModel):
    overall: float = Field(ge=0, le=10, description="Overall offer score out of 10.")
    compensation: float = Field(ge=0, le=10, description="Compensation score.")
    growth: float = Field(ge=0, le=10, description="Growth potential score.")
    work_life: float = Field(ge=0, le=10, description="Work-life balance score.")
    culture: float = Field(ge=0, le=10, description="Company culture score based on available info.")


class OfferEvaluationResult(BaseModel):
    compensation: CompensationAnalysis = Field(description="Compensation analysis.")
    growth: GrowthPotential = Field(description="Growth potential analysis.")
    work_life: WorkLifeBalance = Field(description="Work-life balance analysis.")
    scores: OfferScore = Field(description="Objective scores across dimensions.")
    pros: list[str] = Field(description="List of pros/strengths of this offer.")
    cons: list[str] = Field(description="List of cons/weaknesses of this offer.")
    recommendation: str = Field(
        description="Clear recommendation: 'strongly_recommend', 'recommend', 'neutral', 'caution', 'avoid'."
    )
    recommendation_rationale: str = Field(
        description="Detailed explanation for the recommendation."
    )
    market_benchmarks: str = Field(
        description="Market benchmarks and context used for evaluation."
    )
    negotiation_tips: list[str] = Field(
        default_factory=list,
        description="Specific negotiation tips for this offer."
    )
