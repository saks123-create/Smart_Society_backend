import json
from typing import Optional, List
from app.utils.gemini_client import gemini_generate_json

def triage_complaint(title: str, description: str) -> dict:
    prompt = (
        "You are triaging a residential society complaint. "
        "Return JSON with keys: category, priority, summary. "
        "Priority must be one of: High, Medium, Low. "
        "Category should be short (e.g., Plumbing, Security, Billing, Electricity, Cleanliness, Other). "
        f"Complaint title: {title}\nComplaint description: {description}"
    )
    data = gemini_generate_json(prompt)
    return {
        "category": data.get("category"),
        "priority": data.get("priority"),
        "summary": data.get("summary"),
    }

def draft_notice(prompt_text: str, language: Optional[str] = None) -> dict:
    lang = f"Language: {language}" if language else "Language: English"
    prompt = (
        "You are drafting a professional society notice. "
        "Return JSON with keys: title, body. "
        f"{lang}\n"
        f"Prompt: {prompt_text}"
    )
    data = gemini_generate_json(prompt)
    return {
        "title": data.get("title", "").strip(),
        "body": data.get("body", "").strip(),
    }

def summarize_meeting(transcript: str) -> dict:
    prompt = (
        "Summarize the following society meeting transcript. "
        "Return JSON with keys: summary, action_items (array of short bullet strings). "
        f"Transcript: {transcript}"
    )
    data = gemini_generate_json(prompt)
    action_items = data.get("action_items") or []
    if isinstance(action_items, str):
        action_items = [action_items]
    return {
        "summary": data.get("summary", "").strip(),
        "action_items": action_items,
    }

def chat_response(message: str, context: str) -> dict:
    prompt = (
        "You are a helpful resident assistant for a housing society. "
        "Use the provided context when relevant. "
        "You must strictly follow the visibility limits mentioned in the context. "
        "Do not claim access to records older than or beyond the latest 5 complaints, latest 5 payments, or latest 5 notices. "
        "If the user asks for older records, full history, or details beyond what is present in the context, clearly say you only have the latest 5 visible items and ask them to contact the admin. "
        "When the user asks about notices or announcements, answer from the notice context if available. "
        "If the answer isn't in context, respond generally and advise the resident to contact the admin for confirmation. "
        "Return JSON with keys: reply.\n"
        f"Context:\n{context}\n\n"
        f"User message: {message}"
    )
    data = gemini_generate_json(prompt)
    return {"reply": data.get("reply", "").strip()}

def serialize_action_items(items: Optional[List[str]]) -> Optional[str]:
    if items is None:
        return None
    return json.dumps(items)

def deserialize_action_items(items_text: Optional[str]) -> Optional[List[str]]:
    if not items_text:
        return None
    try:
        data = json.loads(items_text)
        if isinstance(data, list):
            return [str(x) for x in data]
    except Exception:
        pass
    return [items_text]
