"""Schema for the Interview Simulator feature."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class InterviewLevel(str, Enum):
    """The three interviewer personas the frontend can select."""

    FRIENDLY_HR = "friendly_hr"
    TECHNICAL_LEAD = "technical_lead"
    STRESS_INTERVIEW = "stress_interview"


class ConversationTurn(BaseModel):
    """A single past question/answer pair in the interview conversation."""

    question: str = Field(description="The question that was asked.")
    answer: str = Field(description="The candidate's answer to that question.")


class AnswerFeedback(BaseModel):
    """Evaluation of the candidate's most recent answer."""

    strengths: list[str] = Field(description="What the previous answer did well.")
    weaknesses: list[str] = Field(description="What the previous answer lacked.")
    missing_concepts: list[str] = Field(
        description="Relevant concepts the candidate did not mention."
    )
    confidence_level: int = Field(
        ge=0, le=100, description="Perceived confidence in the previous answer, 0-100."
    )
    technical_accuracy: int = Field(
        ge=0, le=100, description="Technical accuracy of the previous answer, 0-100."
    )
    communication_score: int = Field(
        ge=0, le=100, description="Clarity and structure of the previous answer, 0-100."
    )


class FinalEvaluation(BaseModel):
    """Overall evaluation produced once the interview has finished."""

    overall_score: int = Field(ge=0, le=100, description="Overall interview score, 0-100.")
    technical_skills: int = Field(ge=0, le=100, description="Technical skills score, 0-100.")
    communication: int = Field(ge=0, le=100, description="Communication score, 0-100.")
    confidence: int = Field(ge=0, le=100, description="Confidence score, 0-100.")
    problem_solving: int = Field(ge=0, le=100, description="Problem solving score, 0-100.")
    weak_areas: list[str] = Field(description="Areas the candidate should improve.")
    strong_areas: list[str] = Field(description="Areas where the candidate excelled.")
    hiring_recommendation: str = Field(
        description="A short hiring recommendation, e.g. Strong Hire, Hire, No Hire."
    )
    summary: str = Field(
        description="One paragraph explaining the hiring recommendation and overall performance."
    )


class InterviewResponse(BaseModel):
    """Structured output of a single interview turn."""

    interviewer_name: str = Field(description="Name of the persona conducting the interview.")
    interview_level: InterviewLevel = Field(description="The active interview persona.")
    current_question: str = Field(description="The next question posed to the candidate.")
    follow_up_question: str | None = Field(
        default=None,
        description="An optional immediate follow-up to current_question, if the persona probes deeper.",
    )
    expected_topics: list[str] = Field(
        description="Topics or concepts a strong answer to current_question should cover."
    )
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(
        description="Difficulty of current_question."
    )
    feedback_previous_answer: AnswerFeedback | None = Field(
        default=None,
        description="Evaluation of the candidate's previous answer. None on the first question.",
    )
    score_previous_answer: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Score for the candidate's previous answer, 0-100. None on the first question.",
    )
    interview_finished: bool = Field(
        description="True only when the interview has concluded and no further questions follow."
    )
    final_evaluation: FinalEvaluation | None = Field(
        default=None,
        description="Populated only when interview_finished is True.",
    )