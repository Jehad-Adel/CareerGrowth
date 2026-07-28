"""The deterministic layer wrapped around the chains.

Everything here exists because the model gets it wrong: date arithmetic,
totals that disagree with their own parts, extraction debris listed as skills,
and conditional fields that contradict the flag above them. These are the
guards, so they are tested without a model in the loop — the live smoke tests
in tests/ai/ cover the other half.
"""

from datetime import date

import pytest
from google.genai import errors

from app.ai.chains.cv_analysis_chain import _compute_years_of_experience
from app.ai.embeddings import _FALLBACK_RETRY_AFTER, _retry_after
from app.ai.loaders.pdf_loader import clean_extracted_text
from app.ai.schemas.cv_profile import CVProfile, EmploymentPeriod, SeniorityLevel
from app.ai.schemas.job_match_schema import JobMatch
from app.ai.schemas.roadmap_schema import CareerRoadmap
from app.ai.schemas.skill_gap_schema import SkillGapItem


def _period(start, end=None, current=False) -> EmploymentPeriod:
    return EmploymentPeriod(start_date=start, end_date=end, is_current=current)


# --- years of experience -------------------------------------------------


def test_a_simple_span_is_measured_in_years():
    assert _compute_years_of_experience([_period("2020-01", "2023-01")] ) == 3.0


def test_a_year_only_date_is_accepted():
    assert _compute_years_of_experience([_period("2020", "2023")]) == 3.0


def test_concurrent_roles_are_counted_once():
    """The failure this whole pass exists to prevent: two overlapping roles
    read as double the experience."""
    periods = [_period("2020-01", "2023-01"), _period("2021-01", "2022-01")]
    assert _compute_years_of_experience(periods) == 3.0


def test_partially_overlapping_roles_merge():
    periods = [_period("2020-01", "2022-01"), _period("2021-01", "2023-01")]
    assert _compute_years_of_experience(periods) == 3.0


def test_separate_spans_add_up():
    periods = [_period("2015-01", "2016-01"), _period("2020-01", "2022-01")]
    assert _compute_years_of_experience(periods) == 3.0


def test_a_current_role_runs_to_today():
    start = date.today().replace(year=date.today().year - 2)
    years = _compute_years_of_experience(
        [_period(start.strftime("%Y-%m"), None, current=True)]
    )
    assert years == pytest.approx(2.0, abs=0.15)


def test_no_parseable_dates_yields_none_rather_than_a_guess():
    assert _compute_years_of_experience([]) is None
    assert _compute_years_of_experience([_period(None, "2023-01")]) is None
    assert _compute_years_of_experience([_period("last summer", "2023")]) is None


def test_an_inverted_period_is_discarded():
    assert _compute_years_of_experience([_period("2023-01", "2020-01")]) is None


def test_a_future_start_is_discarded():
    ahead = date.today().year + 3
    assert _compute_years_of_experience([_period(f"{ahead}-01", f"{ahead + 1}-01")]) is None


def test_a_future_end_is_clamped_to_today():
    """A typo'd end year must not invent decades of experience."""
    start = date.today().replace(year=date.today().year - 1).strftime("%Y-%m")
    years = _compute_years_of_experience([_period(start, "2099-01")])
    assert years == pytest.approx(1.0, abs=0.15)


def test_an_unparseable_end_discards_the_period():
    assert _compute_years_of_experience([_period("2020-01", "whenever")]) is None


# --- CV profile cleaning -------------------------------------------------


def _profile(**over) -> CVProfile:
    return CVProfile(
        **{
            "seniority_level": SeniorityLevel.MID,
            "skills": [],
            "strengths": [],
            "weaknesses": [],
            "summary": "s",
            "improvement_suggestions": [],
            **over,
        }
    )


def test_extraction_debris_is_dropped_from_skills():
    profile = _profile(skills=["Python", "•", "••", "...", "→→→"])
    assert profile.skills == ["Python"]


def test_one_letter_languages_survive_the_debris_filter():
    """`C` and `R` are real skills. Rejecting every single character, which is
    the obvious implementation, silently deletes two languages."""
    profile = _profile(skills=["C", "R", "Go", "C++", "C#", ".NET", "CI/CD", "Node.js"])
    assert profile.skills == ["C", "R", "Go", "C++", "C#", ".NET", "CI/CD", "Node.js"]


def test_skills_are_deduped_case_insensitively():
    profile = _profile(skills=["Python", " python ", "PYTHON"])
    assert profile.skills == ["Python"]


def test_every_list_field_is_deduped():
    profile = _profile(
        strengths=["Ships fast", "ships fast"],
        weaknesses=["No tests", "no tests"],
        improvement_suggestions=["Add metrics", "add metrics"],
    )
    assert profile.strengths == ["Ships fast"]
    assert profile.weaknesses == ["No tests"]
    assert profile.improvement_suggestions == ["Add metrics"]


# --- job match -----------------------------------------------------------


def _match(skill_matches, **over) -> JobMatch:
    return JobMatch(
        **{
            "match_score": 50,
            "skill_matches": skill_matches,
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "summary": "s",
            **over,
        }
    )


def test_a_matched_skill_cannot_carry_a_gap_severity():
    match = _match(
        [
            {
                "job_skill": "Flask",
                "requirement_level": "Required",
                "matched": True,
                "matched_via": "Django",
                "severity_if_missing": "Blocking",
            }
        ]
    )
    assert match.skill_matches[0].severity_if_missing is None


def test_an_unmatched_skill_cannot_claim_a_source():
    match = _match(
        [
            {
                "job_skill": "Kubernetes",
                "requirement_level": "Required",
                "matched": False,
                "matched_via": "wishful thinking",
                "is_transferable_match": True,
            }
        ]
    )
    item = match.skill_matches[0]
    assert item.matched_via is None
    assert item.is_transferable_match is False
    assert item.severity_if_missing == "Significant"


def test_duplicate_requirements_collapse():
    match = _match(
        [
            {"job_skill": "Go", "requirement_level": "Required", "matched": True},
            {"job_skill": " go ", "requirement_level": "Preferred", "matched": False},
        ]
    )
    assert [i.job_skill for i in match.skill_matches] == ["Go"]


def test_the_flat_skill_lists_still_serialize():
    """The pre-existing API shape. Dropping it would break the jobs page and
    every stored result rendered by it."""
    match = _match(
        [
            {"job_skill": "Python", "requirement_level": "Required", "matched": True},
            {"job_skill": "Kubernetes", "requirement_level": "Required", "matched": False},
        ]
    )
    dumped = match.model_dump(mode="json")
    assert dumped["matched_skills"] == ["Python"]
    assert dumped["missing_skills"] == ["Kubernetes"]


def test_computed_lists_stay_out_of_the_model_schema():
    """`with_structured_output` builds its tool schema from this. A computed
    field appearing here would ask the model to fill in a derived value."""
    properties = JobMatch.model_json_schema()["properties"]
    assert "matched_skills" not in properties
    assert "missing_skills" not in properties


def test_blocking_gaps_are_isolable():
    match = _match(
        [
            {
                "job_skill": "Kubernetes",
                "requirement_level": "Required",
                "matched": False,
                "severity_if_missing": "Blocking",
            },
            {
                "job_skill": "Go",
                "requirement_level": "Preferred",
                "matched": False,
                "severity_if_missing": "Minor",
            },
        ]
    )
    assert [i.job_skill for i in match.blocking_gaps] == ["Kubernetes"]


# --- roadmap -------------------------------------------------------------


def _step(months: float) -> dict:
    return {
        "title": "t",
        "description": "d",
        "skills_to_acquire": [],
        "estimated_duration_months": months,
    }


def test_the_total_is_recomputed_from_the_steps():
    roadmap = CareerRoadmap(
        target_role="Backend Engineer",
        summary="s",
        steps=[_step(2), _step(3.5)],
        # What the model claimed. Deliberately wrong.
        total_estimated_duration_months=99,
    )
    assert roadmap.total_estimated_duration_months == 5.5


def test_an_empty_roadmap_totals_zero():
    roadmap = CareerRoadmap(
        target_role="Backend Engineer",
        summary="Already there.",
        steps=[],
        total_estimated_duration_months=12,
    )
    assert roadmap.total_estimated_duration_months == 0


def test_resources_are_capped():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CareerRoadmap(
            target_role="r",
            summary="s",
            steps=[{**_step(1), "recommended_resources": ["a", "b", "c", "d", "e"]}],
            total_estimated_duration_months=1,
        )


@pytest.mark.parametrize("resources", [[], ["One Resource"]])
def test_too_few_resources_do_not_fail_the_whole_analysis(resources):
    """A hard `min_length=2` turned "the model named one book" into a 502 on a
    call the user had already been charged for. The count is prompt guidance
    now, not a validation gate."""
    item = SkillGapItem(
        skill="Kubernetes",
        priority="High",
        importance_reason="The role runs on it.",
        current_level="None",
        estimated_learning_time="2 months",
        recommended_resources=resources,
        project_to_practice="Deploy a small service.",
        mandatory=True,
    )
    assert item.recommended_resources == resources


# --- PDF text cleaning ---------------------------------------------------


def test_control_characters_are_stripped():
    assert clean_extracted_text("Py\x00thon\x07") == "Python"


def test_dot_leaders_collapse():
    assert clean_extracted_text("Experience.........2020") == "Experience.2020"


def test_short_punctuation_runs_survive():
    """The three-repeat floor is what keeps real tokens intact."""
    assert clean_extracted_text("C++ and --flag") == "C++ and --flag"


def test_column_padding_collapses():
    assert clean_extracted_text("Python      Django") == "Python Django"


def test_blank_line_runs_collapse():
    assert clean_extracted_text("A\n\n\n\n\nB") == "A\n\nB"


def test_whitespace_only_lines_do_not_survive_as_blanks():
    assert clean_extracted_text("A\n   \n   \n   \nB") == "A\n\nB"


def test_cleaning_leaves_real_content_alone():
    text = "Nour Hassan\n\nSenior Engineer at Acme (2020-01 - Present)"
    assert clean_extracted_text(text) == text


# --- embedding quota errors ----------------------------------------------


def test_the_retry_delay_is_read_from_a_real_429():
    """Verbatim from an actual free-tier exhaustion. The delay is buried two
    levels down, tagged by @type, and formatted as a Go duration."""
    payload = {
        "error": {
            "code": 429,
            "status": "RESOURCE_EXHAUSTED",
            "details": [
                {"@type": "type.googleapis.com/google.rpc.Help", "links": []},
                {
                    "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                    "violations": [{"quotaValue": "100"}],
                },
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "29.353643329s",
                },
            ],
        }
    }
    assert _retry_after(errors.ClientError(429, payload)) == pytest.approx(29.35, abs=0.01)


@pytest.mark.parametrize(
    "payload",
    [
        {"error": {"message": "no details at all"}},
        {"error": {"details": []}},
        {"error": {"details": [{"@type": "x/RetryInfo", "retryDelay": "soon"}]}},
        {"error": {"details": [{"@type": "x/Help"}]}},
        {},
    ],
)
def test_an_unreadable_retry_hint_falls_back(payload):
    """Waiting roughly the right amount beats parsing Google's envelope
    perfectly — and beats crashing a three-minute ingest on a missing key."""
    assert _retry_after(errors.ClientError(429, payload)) == _FALLBACK_RETRY_AFTER
