from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# --- Inference Log Schemas ---

class InferenceLogCreate(BaseModel):
    conversation_id: Optional[str] = None
    model: str
    provider: str
    started_at: datetime
    ended_at: datetime
    latency_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    status: str  # "success" | "error"
    error_message: Optional[str] = None
    input_preview: Optional[str] = None
    output_preview: Optional[str] = None


class InferenceLogResponse(BaseModel):
    id: str
    conversation_id: Optional[str]
    model: str
    provider: str
    latency_ms: float
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    status: str
    pii_detected: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Message Schemas ---

class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# --- Conversation Schemas ---

class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True


# --- Chat Schemas ---

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageResponse
    response: MessageResponse


# --- Dashboard Schemas ---

class DashboardStats(BaseModel):
    total_requests: int
    success_rate: float
    avg_latency_ms: float
    total_tokens: int
    error_count: int
    pii_detected_count: int