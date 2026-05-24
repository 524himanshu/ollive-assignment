from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Conversation, Message
from app.schemas.schemas import ChatRequest, ChatResponse, MessageResponse
from app.services.gemini_service import gemini_sdk

router = APIRouter()


def get_conversation_history(conversation_id: str, db: Session) -> list[dict]:
    """Fetch last 10 messages for context window."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(10)
        .all()
    )
    return [{"role": msg.role, "content": msg.content} for msg in messages]


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    # Get or create conversation
    if payload.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.status == "cancelled":
            raise HTTPException(status_code=400, detail="Conversation is cancelled")
    else:
        # Auto-create conversation, title = first 50 chars of message
        conversation = Conversation(
            title=payload.message[:50]
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Fetch history for context
    history = get_conversation_history(conversation.id, db)

    # Call Gemini via SDK
    result = gemini_sdk.chat(
        message=payload.message,
        history=history,
        conversation_id=conversation.id,
    )

    # Save user message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
    )
    db.add(user_msg)

    # Save assistant response
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=result["text"],
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageResponse.model_validate(user_msg),
        response=MessageResponse.model_validate(assistant_msg),
    )