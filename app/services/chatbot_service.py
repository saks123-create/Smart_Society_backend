from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.resident import Resident
from app.models.complaint import Complaint
from app.models.payment import Payment
from app.models.notice import Notice
from app.models.settings import Settings
from app.services.ai_service import chat_response

def _build_context(db: Session, user_id: int) -> str:
    resident = db.query(Resident).filter(Resident.user_id == user_id).first()
    policy_text = None
    settings = db.query(Settings).first()
    if settings:
        policy_text = settings.policy_text

    context_parts = [
        "Chatbot visibility limits:",
        "- You can only see up to the latest 5 complaints for this resident.",
        "- You can only see up to the latest 5 payments for this resident.",
        "- You can only see up to the latest 5 society notices.",
        "- If the user asks for older records, complete history, or anything beyond these limits, tell them to contact the admin.",
    ]
    if resident:
        complaints = (
            db.query(Complaint)
            .filter(Complaint.resident_id == resident.id)
            .order_by(Complaint.created_at.desc())
            .limit(5)
            .all()
        )
        payments = (
            db.query(Payment)
            .filter(Payment.resident_id == resident.id)
            .order_by(Payment.created_at.desc())
            .limit(5)
            .all()
        )
        context_parts.append(f"Resident ID: {resident.id}")
        if complaints:
            context_parts.append("Recent complaints:")
            for c in complaints:
                context_parts.append(
                    f"- {c.title} (status: {c.status}, category: {c.category or 'N/A'}, priority: {c.priority or 'N/A'})"
                )
        if payments:
            context_parts.append("Recent payments:")
            for p in payments:
                context_parts.append(
                    f"- amount: {p.amount}, status: {p.status}, due: {p.due_date or 'N/A'}"
                )

    notices = db.query(Notice).order_by(Notice.created_at.desc()).limit(5).all()
    if notices:
        context_parts.append("Latest notices:")
        for n in notices:
            context_parts.append(f"- {n.title}: {n.content}")

    if policy_text:
        context_parts.append("Society policies:")
        context_parts.append(policy_text)

    return "\n".join(context_parts) if context_parts else "No relevant context available."

def _is_beyond_visible_limit(message: str) -> bool:
    lowered = (message or "").lower()
    limit_phrases = [
        "all payments",
        "all notices",
        "all complaints",
        "older payments",
        "older notices",
        "older complaints",
        "complete payment",
        "complete notice",
        "complete complaint",
        "full payment",
        "full notice",
        "full complaint",
        "entire payment",
        "entire notice",
        "entire complaint",
        "payment history",
        "notice history",
        "complaint history",
        "more than 5",
        "more than five",
        "previous notices",
        "previous payments",
        "previous complaints",
        "older than",
        "before that",
    ]
    return any(phrase in lowered for phrase in limit_phrases)

def _fallback_chat_reply(message: str, context: str) -> str:
    message_text = (message or "").strip()
    lowered = message_text.lower()

    if not message_text:
        return "Please type your question and try again."

    if _is_beyond_visible_limit(message_text):
        return (
            "I can only access the latest 5 payments, complaints, and notices available to me. "
            "For older records or complete history, please contact the admin."
        )

    if any(word in lowered for word in ["complaint", "issue", "problem", "maintenance"]):
        if "Recent complaints:" in context:
            return (
                "I could not reach the AI service right now, but I can only refer to your latest 5 complaints. "
                "Please check the Complaints section for the latest status, or contact the admin for older records."
            )
        return "I could not reach the AI service right now. You can still raise or review complaints from the Complaints section."

    if any(word in lowered for word in ["payment", "bill", "maintenance due", "due amount", "dues"]):
        if "Recent payments:" in context:
            return (
                "I could not reach the AI service right now, but I can only refer to your latest 5 payments. "
                "Please open the Payments section to check the latest status and due dates, or contact the admin for older records."
            )
        return "I could not reach the AI service right now. Please open the Payments section to review your dues and payment history."

    if any(word in lowered for word in ["notice", "notices", "announcement", "announcements", "update", "updates", "guideline", "guidelines", "rule", "rules"]):
        if "Latest notices:" in context:
            return (
                "I could not reach the AI service right now, but I can only refer to the latest 5 notices. "
                "Please open Announcements to view the newest updates, or contact the admin for older notices."
            )
        return "I could not reach the AI service right now. Please check the Announcements section for recent updates."

    return "AI service is temporarily unavailable. Please ask about payments, complaints, notices, or check the related section in the app."

def handle_chat(db: Session, user_id: int, message: str) -> dict:
    context = _build_context(db, user_id)
    try:
        return chat_response(message, context)
    except HTTPException as exc:
        if exc.status_code == 503:
            return {"reply": "AI service is not configured yet. Please contact the admin."}
        return {"reply": _fallback_chat_reply(message, context)}
