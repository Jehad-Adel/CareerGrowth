"""Schema for the Cover Letter feature."""

from typing import Literal

from pydantic import BaseModel, Field, computed_field, model_validator

Tone = Literal["Formal", "Conversational", "Enthusiastic"]

# Recruiters skim. Past roughly this length a letter stops being read, and a
# model left unbounded will happily produce two pages.
MAX_BODY_PARAGRAPHS = 4


class CoverLetter(BaseModel):
    """A letter written from the candidate's real CV against one job.

    Structured rather than one blob of prose so the UI can render it, the user
    can edit a single paragraph, and the export can lay it out — none of which
    is possible if the model just returns text.
    """

    greeting: str = Field(
        description=(
            "Salutation line. Use the hiring manager's name only if the job "
            "description states it; otherwise a role-appropriate neutral greeting. "
            "Never invent a name."
        )
    )
    opening: str = Field(
        description=(
            "One paragraph naming the specific role and the single strongest, "
            "concrete reason this candidate fits it. No throat-clearing."
        )
    )
    body: list[str] = Field(
        max_length=MAX_BODY_PARAGRAPHS,
        description=(
            "One to three paragraphs of evidence, each tying a real achievement "
            "from the CV to a stated requirement of the job."
        ),
    )
    closing: str = Field(
        description="One short paragraph with a clear, non-presumptuous call to action."
    )
    sign_off: str = Field(
        description="Closing line such as 'Sincerely' — the name is appended by the app, not you."
    )
    tone: Tone = Field(
        default="Formal",
        description="The register the letter was written in, matching what the job description signals.",
    )
    evidence_used: list[str] = Field(
        default_factory=list,
        description=(
            "The specific CV facts this letter leans on, so the candidate can "
            "verify nothing was invented on their behalf."
        ),
    )
    word_count_note: str = Field(
        default="",
        description="One sentence on why the letter is the length it is.",
    )

    @model_validator(mode="after")
    def _tidy(self) -> "CoverLetter":
        """Drop empty paragraphs the model sometimes pads the list with."""
        self.body = [p.strip() for p in self.body if p and p.strip()]
        self.evidence_used = [e.strip() for e in self.evidence_used if e and e.strip()]
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_text(self) -> str:
        """The letter as plain text, ready to copy or download.

        Assembled server-side so the clipboard button, the .txt export and any
        future PDF all render identically — three places reimplementing this
        join is three places to drift.
        """
        parts = [self.greeting, "", self.opening, ""]
        for paragraph in self.body:
            parts.extend([paragraph, ""])
        parts.extend([self.closing, "", self.sign_off])
        return "\n".join(parts).strip()
