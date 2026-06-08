from pydantic import BaseModel
from typing import Optional, List

class NoticeDraftRequest(BaseModel):
    prompt: str
    language: Optional[str] = None

class NoticeDraftResponse(BaseModel):
    title: str
    body: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    sources: Optional[List[str]] = None
