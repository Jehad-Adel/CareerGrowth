import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.chains.offer_eval_chain import build_offer_eval_chain
from app.ai import embeddings
from app.errors import AppError, NoCvOnProfile
from app.logging import get_logger
from app.models import CareerProfile, OfferEvaluation, Skill
from app.services import knowledge_service, quota_service, rag_service, xp_service

log = get_logger(__name__)

FEATURE = "offer_evaluation"
PAGE_SIZE = 50


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


def _profile_summary(db: Session, profile_id: uuid.UUID) -> str:
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")

    skills = db.execute(
        select(Skill).where(Skill.profile_id == profile_id)
    ).scalars()

    lines = [
        f"Current role: {profile.current_role or 'unknown'}",
        f"Target role: {profile.target_role or 'not set'}",
        f"Years of experience: {profile.years_of_experience or 'unknown'}",
        f"Seniority level: {profile.seniority_level or 'unknown'}",
        f"Summary: {profile.summary or 'not provided'}",
    ]
    skill_names = [s.name for s in skills]
    lines.append(f"Skills: {', '.join(skill_names) if skill_names else 'none recorded'}")
    return "\n".join(lines)


def evaluate(
    db: Session,
    profile_id: uuid.UUID,
    *,
    company: str,
    role_title: str,
    offer_details: str,
) -> OfferEvaluation:
    profile = db.get(CareerProfile, profile_id)
    if profile is None:
        raise ValueError(f"No profile {profile_id}")

    profile_summary = _profile_summary(db, profile_id)

    # RAG retrieval for market context
    market_context = ""
    try:
        query_vector = embeddings.embed_query(offer_details)
        knowledge_chunks = knowledge_service.retrieve(
            db, f"Market compensation {role_title} {company}", vector=query_vector
        )
        market_context = knowledge_service.build_context(knowledge_chunks)
    except Exception:
        log.exception("knowledge_retrieve_failed", profile_id=str(profile_id))
        market_context = "No specific market data available."

    quota_service.consume(db, profile_id, FEATURE)

    try:
        result = build_offer_eval_chain().invoke(
            {
                "offer_details": offer_details,
                "profile_summary": profile_summary,
                "market_context": market_context,
            }
        )
    except Exception as exc:
        log.exception("offer_eval_chain_failed", profile_id=str(profile_id))
        raise AnalysisFailed(
            "Could not evaluate that offer. Try again shortly."
        ) from exc

    record = OfferEvaluation(
        profile_id=profile_id,
        company=company.strip(),
        role_title=role_title.strip(),
        offer_details=offer_details.strip(),
        result=result.model_dump(mode="json"),
        overall_score=result.scores.overall,
        recommendation=result.recommendation,
    )
    db.add(record)
    db.flush()

    try:
        rag_service.ingest(
            db,
            profile_id,
            "offer_evaluation",
            f"Offer evaluation for {role_title} at {company}\n\n"
            f"Scores: {result.scores.model_dump()}\n\n"
            f"Pros: {'; '.join(result.pros)}\n"
            f"Cons: {'; '.join(result.cons)}\n"
            f"Recommendation: {result.recommendation}",
            source_id=record.id,
        )
    except Exception:
        log.exception("rag_ingest_failed", kind="offer", profile_id=str(profile_id))

    xp_service.record_event(
        db,
        profile_id,
        "offer_evaluated",
        {
            "offer_id": str(record.id),
            "company": company,
            "role": role_title,
            "score": record.overall_score,
        },
        xp=xp_service.XP_AWARDS.get("offer_evaluated", 35),
    )

    db.commit()
    db.refresh(record)
    return record


def latest(db: Session, profile_id: uuid.UUID) -> OfferEvaluation | None:
    return db.execute(
        select(OfferEvaluation)
        .where(OfferEvaluation.profile_id == profile_id)
        .order_by(OfferEvaluation.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()


def list_history(
    db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE
) -> list[OfferEvaluation]:
    return list(
        db.execute(
            select(OfferEvaluation)
            .where(OfferEvaluation.profile_id == profile_id)
            .order_by(OfferEvaluation.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def get(
    db: Session, profile_id: uuid.UUID, offer_id: uuid.UUID
) -> OfferEvaluation | None:
    return db.execute(
        select(OfferEvaluation).where(
            OfferEvaluation.id == offer_id,
            OfferEvaluation.profile_id == profile_id,
        )
    ).scalar_one_or_none()
