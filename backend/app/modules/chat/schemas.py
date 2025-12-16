"""
Chat schemas
"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatContext(BaseModel):
    current_page: Optional[str] = None
    selected_restaurant: Optional[str] = None


class ChatMessageMetadata(BaseModel):
    restaurants: Optional[List[Any]] = None
    booking_info: Optional[dict] = None
    suggestions: Optional[List[str]] = None


# Request Schemas
class SendMessageRequest(BaseModel):
    chat_id: Optional[str] = None
    message: str
    context: Optional[ChatContext] = None


# Response Schemas
class ChatMessageResponse(BaseModel):
    id: str
    chat_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[ChatMessageMetadata] = None
    
    class Config:
        from_attributes = True


class SendMessageResponse(BaseModel):
    chat_id: str
    message: ChatMessageResponse
    suggestions: Optional[List[str]] = None


class ChatSessionResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatSessionDetailResponse(ChatSessionResponse):
    messages: List[ChatMessageResponse] = []
