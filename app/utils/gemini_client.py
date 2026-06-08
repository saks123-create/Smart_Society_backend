import os
import json
import logging
from typing import Any, Optional
import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def _extract_text(payload: dict) -> str:
    try:
        return payload["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return ""

def _safe_json(text: str) -> Optional[dict]:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        # Try to find first JSON object in text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
    return None

def gemini_generate_json(prompt: str) -> dict:
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="AI is not configured")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload: dict[str, Any] = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    try:
        response = httpx.post(url, json=payload, timeout=20.0)
    except httpx.RequestError as exc:
        logger.warning("Gemini request failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI request failed. Please check network or API configuration.")

    if response.status_code >= 400:
        error_detail = ""
        try:
            error_payload = response.json()
            error_detail = (
                error_payload.get("error", {}).get("message")
                or error_payload.get("message")
                or ""
            )
        except Exception:
            error_detail = response.text[:200]
        logger.warning("Gemini returned %s: %s", response.status_code, error_detail or "No details")
        detail = f"AI request failed ({response.status_code})."
        if error_detail:
            detail = f"{detail} {error_detail}"
        raise HTTPException(status_code=502, detail=detail)

    data = response.json()
    text = _extract_text(data)
    parsed = _safe_json(text)
    if not parsed:
        logger.warning("Gemini returned invalid JSON payload")
        raise HTTPException(status_code=502, detail="AI response invalid")
    return parsed
