"""Chain for the CV Analysis feature.

Orchestration: prompt -> structured-output LLM -> deterministic post-pass.

The one piece of logic here is recomputing `years_of_experience` from the
dates the model extracted. LLM date arithmetic is unreliable in both
directions — it double-counts concurrent roles and silently rounds — and the
figure feeds the profile, the roadmap, and every seniority judgement after it.
Everything else stays parsing-free.
"""

from datetime import date, datetime

from langchain_core.runnables import Runnable, RunnableLambda

from app.ai.llm.gemini import get_gemini_model
from app.ai.prompts.cv_analysis_prompt import CV_ANALYSIS_PROMPT
from app.ai.schemas.cv_profile import CVProfile, EmploymentPeriod

# The prompt asks for "YYYY-MM" or "YYYY". The full-date form is tolerated
# because models emit it anyway when the CV states one.
_DATE_FORMATS = ("%Y-%m", "%Y", "%Y-%m-%d")

_DAYS_PER_YEAR = 365.25


def _parse_period_date(value: str | None) -> date | None:
    """Parse a period endpoint into a date. None if absent or unparseable."""
    if not value:
        return None
    value = value.strip()
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        return date(parsed.year, parsed.month, parsed.day if fmt == "%Y-%m-%d" else 1)
    return None


def _period_bounds(period: EmploymentPeriod) -> tuple[date, date] | None:
    """Resolve a period to (start, end). None when it cannot be trusted.

    A missing start, an unparseable end, or an end before its start all yield
    None rather than a guess — a wrong interval would silently inflate the
    total, which is the failure this whole pass exists to prevent.
    """
    start = _parse_period_date(period.start_date)
    if start is None:
        return None

    today = date.today()
    # A start in the future is an extraction error, not a job not yet begun.
    if start > today:
        return None

    if period.is_current or period.end_date is None:
        end = today
    else:
        end = _parse_period_date(period.end_date)
        if end is None:
            return None

    return (start, min(end, today)) if end >= start else None


def _compute_years_of_experience(periods: list[EmploymentPeriod]) -> float | None:
    """Total non-overlapping employment, in years.

    Overlapping periods (concurrent roles, a promotion listed as its own
    entry) are merged so time is counted once. Returns None when no period
    has a usable start date, matching the rule that experience is never
    inferred without explicit dates.
    """
    intervals = sorted(
        bounds for period in periods if (bounds := _period_bounds(period)) is not None
    )
    if not intervals:
        return None

    merged: list[tuple[date, date]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    total_days = sum((end - start).days for start, end in merged)
    return round(total_days / _DAYS_PER_YEAR, 1)


def _apply_deterministic_experience(profile: CVProfile) -> CVProfile:
    """Replace the model's own total with one computed from its dates."""
    profile.years_of_experience = _compute_years_of_experience(
        profile.employment_periods
    )
    return profile


def build_cv_analysis_chain() -> Runnable:
    """Build and return the CV Analysis Runnable chain."""
    structured_llm = get_gemini_model().with_structured_output(CVProfile)
    return (
        CV_ANALYSIS_PROMPT
        | structured_llm
        | RunnableLambda(_apply_deterministic_experience)
    )
