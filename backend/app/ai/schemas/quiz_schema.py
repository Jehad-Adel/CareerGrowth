from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    question: str = Field(description="The question to ask.")
    options: list[str] = Field(
        description="4 possible answers as a list of strings.",
        min_length=4,
        max_length=4,
    )
    correct_answer: int = Field(
        ge=0,
        le=3,
        description="Index (0-3) of the correct option in the options list.",
    )
    explanation: str = Field(
        description="Brief explanation of why the correct answer is right."
    )


class QuizResponse(BaseModel):
    questions: list[QuizQuestion] = Field(
        description="List of quiz questions.",
        min_length=1,
        max_length=20,
    )
    overall_context: str = Field(
        default="",
        description="Optional context about what this quiz covers.",
    )


class AnswerEvaluation(BaseModel):
    results: list[dict] = Field(
        description="Evaluation results for each answer."
    )
    overall_feedback: str = Field(
        description="Summary feedback on the overall performance."
    )
