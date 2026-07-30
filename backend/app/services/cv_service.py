import uuid
from io import BytesIO

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.cv_analysis_chain import build_cv_analysis_chain
from app.ai.loaders.pdf_loader import load_pdf_bytes
from app.ai.schemas.cv_profile import CVProfile
from app.ai import embeddings
from app.errors import AppError
from app.logging import get_logger
from app.models import CvAnalysis
from app.schemas.profile import SkillIn
from app.services import knowledge_service, profile_service, quota_service, rag_service, xp_service

log = get_logger(__name__)

FEATURE = "cv_analysis"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_PAGES = 20
PDF_MAGIC = b"%PDF-"

# Mastery for a skill the CV demonstrates. Not 100: the CV proves the skill
# exists, not that it is mastered. Later signals raise it; nothing lowers it.
CV_SKILL_MASTERY = 40


class UnsupportedFile(AppError):
    status_code = 415
    code = "unsupported_file"


class FileTooLarge(AppError):
    status_code = 413
    code = "file_too_large"


class UnreadableCv(AppError):
    status_code = 422
    code = "unreadable_cv"


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


def validate_upload(filename: str | None, content: bytes) -> None:
    """Reject anything that is not a small, genuine PDF.

    Checked server-side and by content, not by the filename or the
    Content-Length header — both are attacker-controlled.
    """
    if len(content) > MAX_UPLOAD_BYTES:
        raise FileTooLarge(
            f"That file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
            limit_bytes=MAX_UPLOAD_BYTES,
        )
    if not content:
        raise UnsupportedFile("That file is empty.")
    if not content.startswith(PDF_MAGIC):
        # A .docx renamed to .pdf fails here, which is the point.
        raise UnsupportedFile("Upload a PDF. Other formats are not supported yet.")


def analyze(
    db: Session, profile_id: uuid.UUID, filename: str | None, content: bytes
) -> CvAnalysis:
    """Extract a CV, write it onto the profile, and record the growth.

    The uploaded file is never persisted — parse-and-discard. Only the
    extracted text reaches the database, on `career_profiles.cv_text`.
    """
    validate_upload(filename, content)

    try:
        cv_text = load_pdf_bytes(BytesIO(content), max_pages=MAX_PAGES)
    except ValueError as exc:
        raise UnreadableCv(str(exc)) from exc

    # Charge the quota before the call: a failed generation still costs tokens.
    quota_service.consume(db, profile_id, FEATURE)

    # Retrieve RAG context for CV-writing best practices
    try:
        from app.services.hybrid_rag import retrieve_context
        rag_context = retrieve_context(db, profile_id, "CV writing best practices", max_chars=2000)
    except Exception:
        rag_context = ""
        log.exception("hybrid_rag_failed", feature="cv_analysis")

    try:
        result: CVProfile = build_cv_analysis_chain().invoke(
            {"cv_text": cv_text}
        )
    except Exception as exc:
        # Never leak provider internals or the prompt to the client.
        log.exception("cv_analysis_chain_failed", profile_id=str(profile_id))
        raise AnalysisFailed(
            "The analysis service could not process that CV. Try again shortly."
        ) from exc

    analysis = CvAnalysis(
        profile_id=profile_id,
        result=result.model_dump(mode="json"),
        skills_found=len(result.skills),
    )
    db.add(analysis)
    db.flush()

    # The spine: the CV writes the canonical profile, and every later feature
    # reads from there rather than asking for the CV again.
    profile = profile_service.set_cv_extract(db, profile_id, cv_text, result)
    profile_service.upsert_skills(
        db,
        profile.id,
        [SkillIn(name=name, mastery=CV_SKILL_MASTERY) for name in result.skills],
        source="cv",
    )
    xp_service.record_event(
        db,
        profile_id,
        "cv_analyzed",
        {"analysis_id": str(analysis.id), "skills_found": analysis.skills_found},
        xp=xp_service.XP_AWARDS["cv_analyzed"],
    )

    # Feed the chat corpus. Best-effort on purpose: a RAG failure must not
    # throw away an analysis the user already spent a quota call on.
    try:
        rag_service.ingest(
            db, profile_id, "cv", cv_text, title="CV", source_id=analysis.id
        )
    except Exception:
        log.exception("rag_ingest_failed", kind="cv", profile_id=str(profile_id))

    db.refresh(analysis)
    return analysis


def latest(db: Session, profile_id: uuid.UUID) -> CvAnalysis | None:
    return db.execute(
        select(CvAnalysis)
        .where(CvAnalysis.profile_id == profile_id)
        .order_by(CvAnalysis.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
