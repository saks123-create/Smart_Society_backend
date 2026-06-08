from sqlalchemy.orm import Session
from typing import Optional
from app.models.meeting_summary import MeetingSummary
from app.schemas.meeting_summary import MeetingSummaryCreate
from app.services.admin_audit_service import log_admin_action
from app.services.ai_service import summarize_meeting, serialize_action_items, deserialize_action_items

def list_meeting_summaries(db: Session, offset: int = 0, limit: Optional[int] = None):
    query = db.query(MeetingSummary).order_by(MeetingSummary.created_at.desc())
    summaries = query.all() if limit is None else query.offset(offset).limit(limit).all()
    results = []
    for item in summaries:
        results.append(
            {
                "id": item.id,
                "title": item.title,
                "transcript": item.transcript,
                "summary": item.summary,
                "action_items": deserialize_action_items(item.action_items),
                "created_by_user_id": item.created_by_user_id,
                "created_at": item.created_at,
            }
        )
    return results

def create_meeting_summary(
    db: Session,
    data: MeetingSummaryCreate,
    user_id: int | None = None,
    actor_user_id: int | None = None,
):
    ai = summarize_meeting(data.transcript)
    summary = ai.get("summary") or ""
    action_items = ai.get("action_items")
    meeting = MeetingSummary(
        title=data.title,
        transcript=data.transcript,
        summary=summary,
        action_items=serialize_action_items(action_items),
        created_by_user_id=user_id,
    )
    db.add(meeting)
    db.flush()
    audit_actor_id = actor_user_id if actor_user_id is not None else user_id
    if audit_actor_id is not None:
        log_admin_action(
            db,
            actor_user_id=audit_actor_id,
            action="meeting.created",
            target_type="meeting_summary",
            target_id=meeting.id,
            details={"title": meeting.title},
        )
    db.commit()
    db.refresh(meeting)
    return {
        "id": meeting.id,
        "title": meeting.title,
        "transcript": meeting.transcript,
        "summary": meeting.summary,
        "action_items": deserialize_action_items(meeting.action_items),
        "created_by_user_id": meeting.created_by_user_id,
        "created_at": meeting.created_at,
    }
