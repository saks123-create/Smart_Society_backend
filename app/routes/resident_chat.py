from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.chatbot_service import handle_chat
from app.utils.deps import get_db, require_roles, get_current_user
from app.models.user import UserRole

router = APIRouter(prefix="/resident/chat", tags=["resident", "chat"])

@router.post("/", response_model=ChatResponse, dependencies=[Depends(require_roles([UserRole.resident, UserRole.admin]))])
def chat(data: ChatRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    response = handle_chat(db, current_user.id, data.message)
    return {"reply": response.get("reply", "")}
