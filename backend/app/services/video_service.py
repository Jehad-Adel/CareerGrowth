import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session
from youtube_transcript_api import (
    InvalidVideoId,
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

from app.ai.chains.video_summary_chain import build_video_summary_chain
from app.ai.sanitizer import sanitize_untrusted_text
from app.errors import AppError
from app.logging import get_logger
from app.models import VideoSummary
from app.services import quota_service, rag_service, xp_service

log = get_logger(__name__)

FEATURE = "video_summary"
PAGE_SIZE = 50
PREFERRED_LANGUAGES = ("en", "en-US", "en-GB", "ar")


class AnalysisFailed(AppError):
    status_code = 502
    code = "analysis_failed"


class UnsupportedUrl(AppError):
    status_code = 422
    code = "unsupported_url"


def _extract_youtube_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})",
        r"(?:youtube\.com/embed/)([\w-]{11})",
        r"(?:youtube\.com/shorts/)([\w-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _detect_source(url: str) -> str:
    if "youtube" in url.lower() or "youtu.be" in url.lower():
        return "youtube"
    if "vimeo" in url.lower():
        return "vimeo"
    return "other"


def _fetch_transcript(url: str) -> str:
    video_id = _extract_youtube_id(url)
    if not video_id:
        raise UnsupportedUrl(
            "Could not extract a video ID from that URL. "
            "Supported formats: YouTube (watch, short, embed, youtu.be)."
        )

    try:
        available = YouTubeTranscriptApi().list(video_id)
        try:
            transcript = available.find_transcript(PREFERRED_LANGUAGES)
        except NoTranscriptFound:
            # Any language beats no summary -- the model reads it either way.
            transcript = next(iter(available))
        fetched = transcript.fetch()
    except TranscriptsDisabled as exc:
        raise UnsupportedUrl(
            "That video has captions turned off, so there is no transcript "
            "to summarize. Try another video."
        ) from exc
    except (NoTranscriptFound, StopIteration) as exc:
        raise UnsupportedUrl(
            "That video has no transcript available. Try another video."
        ) from exc
    except (VideoUnavailable, InvalidVideoId) as exc:
        raise UnsupportedUrl(
            "That video is unavailable. Check the link and try again."
        ) from exc
    except (IpBlocked, RequestBlocked) as exc:
        log.warning("youtube_blocked_our_ip", video_id=video_id)
        raise AnalysisFailed(
            "Could not reach YouTube for that video right now. "
            "Try again shortly."
        ) from exc
    except Exception as exc:
        log.exception("youtube_transcript_fetch_failed", video_id=video_id)
        raise AnalysisFailed(
            "Could not fetch the transcript for that video. "
            "Try again shortly."
        ) from exc

    return " ".join(snippet.text for snippet in fetched)


def process(
    db: Session,
    profile_id: uuid.UUID,
    *,
    url: str,
    mode: str = "summary",
) -> VideoSummary:
    source_type = _detect_source(url)
    transcript = _fetch_transcript(url)

    if mode == "transcript":
        record = VideoSummary(
            profile_id=profile_id,
            url=url,
            source_type=source_type,
            mode=mode,
            transcript=transcript,
        )
        db.add(record)
        xp_service.record_event(
            db,
            profile_id,
            "video_transcribed",
            {"video_id": str(record.id)},
            xp=xp_service.XP_AWARDS.get("video_transcribed", 5),
        )
        db.commit()
        db.refresh(record)
        return record

    try:
        with quota_service.consume_and_refund_on_error(db, profile_id, FEATURE):
            result = build_video_summary_chain().invoke(
                {
                    "transcript": sanitize_untrusted_text(
                        transcript, tag="transcript"
                    )
                }
            )
    except AppError:
        raise
    except Exception as exc:
        log.exception("video_summary_chain_failed", profile_id=str(profile_id))
        raise AnalysisFailed(
            "Could not summarize that video. Try again shortly."
        ) from exc

    record = VideoSummary(
        profile_id=profile_id,
        url=url,
        title=result.title,
        source_type=source_type,
        mode=mode,
        transcript=transcript,
        summary=result.summary,
        key_takeaways=list(result.key_takeaways),
    )
    db.add(record)
    db.flush()

    try:
        rag_service.ingest(
            db,
            profile_id,
            "video_summary",
            f"Video: {result.title}\n\n{result.summary}\n\n"
            + "\n".join(f"- {p}" for p in result.summary_points),
            source_id=record.id,
        )
    except Exception:
        log.exception("rag_ingest_failed", kind="video", profile_id=str(profile_id))

    xp_service.record_event(
        db,
        profile_id,
        "video_summarized",
        {"video_id": str(record.id), "title": result.title},
        xp=xp_service.XP_AWARDS.get("video_summarized", 15),
    )

    db.commit()
    db.refresh(record)
    return record


def history(
    db: Session, profile_id: uuid.UUID, limit: int = PAGE_SIZE
) -> list[VideoSummary]:
    return list(
        db.execute(
            select(VideoSummary)
            .where(VideoSummary.profile_id == profile_id)
            .order_by(VideoSummary.created_at.desc())
            .limit(limit)
        ).scalars()
    )


def get(
    db: Session, profile_id: uuid.UUID, video_id: uuid.UUID
) -> VideoSummary | None:
    return db.execute(
        select(VideoSummary).where(
            VideoSummary.id == video_id,
            VideoSummary.profile_id == profile_id,
        )
    ).scalar_one_or_none()
