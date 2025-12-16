"""
Chat API routes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_id, get_current_user_id_optional
from app.modules.chat.models import ChatSession, ChatMessage, MessageRole
from app.modules.restaurants.models import Restaurant
from app.modules.chat.schemas import (
    SendMessageRequest,
    SendMessageResponse,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionDetailResponse
)
from app.shared.schemas import success_response, error_response
from typing import Optional

router = APIRouter(prefix="/chat", tags=["Chat"])


# Simple chatbot responses (in production, integrate with AI service)
CHATBOT_RESPONSES = {
    "xin chào": "Xin chào! Tôi là trợ lý ảo của Smart Travel System. Tôi có thể giúp bạn tìm nhà hàng, đặt bàn, hoặc trả lời các câu hỏi về ẩm thực. Bạn cần gì?",
    "hello": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?",
    "tìm nhà hàng": "Bạn muốn tìm nhà hàng loại nào? Phở, bún, bánh mì, hay hải sản?",
    "đặt bàn": "Để đặt bàn, bạn cần cho tôi biết: 1) Nhà hàng bạn muốn đặt, 2) Ngày giờ, 3) Số khách. Hoặc bạn có thể vào trang nhà hàng và nhấn nút 'Đặt bàn'.",
    "phở": "Tôi tìm thấy một số quán phở ngon:\n\n1. **Phở Hà Nội** - Rating: 4.8⭐\n2. **Phở Sài Gòn** - Rating: 4.5⭐\n\nBạn muốn xem chi tiết quán nào?",
    "cảm ơn": "Không có gì! Nếu cần gì thêm, đừng ngại hỏi tôi nhé! 😊",
    "default": "Tôi hiểu bạn đang hỏi về '{query}'. Tôi có thể giúp bạn:\n\n• Tìm nhà hàng theo loại ẩm thực\n• Đặt bàn nhà hàng\n• Xem đánh giá và menu\n• Tìm đường đến nhà hàng\n\nBạn muốn tôi giúp gì?"
}


def get_chatbot_response(message: str) -> tuple[str, list]:
    """Simple chatbot logic - replace with AI in production"""
    message_lower = message.lower().strip()
    
    suggestions = []
    
    for key, response in CHATBOT_RESPONSES.items():
        if key in message_lower:
            if key == "phở":
                suggestions = ["Xem Phở Hà Nội", "Đặt bàn ngay", "Tìm quán khác"]
            elif key == "tìm nhà hàng":
                suggestions = ["Phở", "Bún", "Bánh mì", "Hải sản", "Cơm"]
            elif key in ["xin chào", "hello"]:
                suggestions = ["Tìm nhà hàng", "Đặt bàn", "Xem đánh giá"]
            return response, suggestions
    
    return CHATBOT_RESPONSES["default"].format(query=message), ["Tìm nhà hàng", "Đặt bàn", "Liên hệ hỗ trợ"]


@router.post("/message", response_model=dict)
async def send_message(
    request: SendMessageRequest,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to chatbot"""
    # Get or create chat session
    if request.chat_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == request.chat_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return error_response("E3001", "Không tìm thấy phiên chat")
    else:
        # Create new session
        session = ChatSession(
            user_id=user_id,
            title=request.message[:50] + "..." if len(request.message) > 50 else request.message
        )
        db.add(session)
        await db.flush()
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.USER,
        content=request.message
    )
    db.add(user_message)
    await db.flush()
    
    # Generate bot response
    bot_response, suggestions = get_chatbot_response(request.message)
    
    # Save bot message
    bot_message = ChatMessage(
        session_id=session.id,
        role=MessageRole.ASSISTANT,
        content=bot_response,
        message_metadata={"suggestions": suggestions}
    )
    db.add(bot_message)
    await db.flush()
    await db.refresh(bot_message)
    
    # Update session
    session.updated_at = datetime.utcnow()
    await db.flush()
    
    return success_response(
        data={
            "chat_id": session.id,
            "message": {
                "id": bot_message.id,
                "chat_id": session.id,
                "role": bot_message.role.value,
                "content": bot_message.content,
                "timestamp": bot_message.created_at.isoformat(),
                "metadata": bot_message.message_metadata
            },
            "suggestions": suggestions
        },
        message="OK"
    )


@router.get("/history", response_model=dict)
async def get_chat_history(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat history"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    return success_response(
        data=[{
            "id": s.id,
            "title": s.title,
            "updated_at": s.updated_at.isoformat()
        } for s in sessions],
        message="Lấy lịch sử chat thành công"
    )


@router.get("/{chat_id}", response_model=dict)
async def get_chat_session(
    chat_id: str,
    user_id: Optional[str] = Depends(get_current_user_id_optional),
    db: AsyncSession = Depends(get_db)
):
    """Get chat session with messages"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == chat_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response("E3001", "Không tìm thấy phiên chat")
    
    # Get messages
    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_id)
        .order_by(ChatMessage.created_at)
    )
    messages = msg_result.scalars().all()
    
    return success_response(
        data={
            "id": session.id,
            "title": session.title,
            "messages": [{
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "timestamp": m.created_at.isoformat(),
                "metadata": m.message_metadata
            } for m in messages]
        },
        message="Lấy phiên chat thành công"
    )


@router.delete("/{chat_id}", response_model=dict)
async def delete_chat_session(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == chat_id,
            ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        return error_response("E3001", "Không tìm thấy phiên chat")
    
    # Delete messages first
    msg_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == chat_id)
    )
    for msg in msg_result.scalars().all():
        await db.delete(msg)
    
    await db.delete(session)
    await db.flush()
    
    return success_response(
        data=None,
        message="Xóa phiên chat thành công"
    )
