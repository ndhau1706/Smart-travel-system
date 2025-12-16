"""
Chat routes for the chatbot API.
"""
from fastapi import APIRouter, HTTPException
from models import ChatRequest, ChatResponse, RestaurantInfo
from services import rag_pipeline, session_manager
from utils import detect_language
import uuid

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return AI response.
    
    Args:
        request: Chat request with message and optional session_id
        
    Returns:
        Chat response with AI message and restaurant recommendations
    """
    try:
        # Create or get session
        if not request.session_id:
            language = detect_language(request.message)
            session_id = await session_manager.create_session(
                user_id=request.user_id,
                title=request.message[:50],
                language=language
            )
        else:
            session_id = request.session_id
            session = await session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        
        # Note: Authentication and message limits are handled by parent module
        # This module only handles chat functionality
        
        # Save user message
        await session_manager.add_message(
            session_id=session_id,
            role="user",
            content=request.message
        )
        
        # Prepare user context with location if provided
        user_context = {}
        if request.user_location:
            user_context['user_location'] = request.user_location
        
        # Process through RAG pipeline
        result = await rag_pipeline.process(request.message, user_context=user_context)
        
        # Ensure result is not None and is a dictionary
        if result is None:
            result = {
                "message": "Xin lỗi, tôi gặp lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại.",
                "restaurants": [],
                "language": "vi"
            }
        elif not isinstance(result, dict):
            raise HTTPException(status_code=500, detail=f"RAG pipeline returned {type(result).__name__} instead of dict")
        
        # Save assistant message
        await session_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=result.get("message", ""),
            metadata={
                "restaurants": [r.get("id") for r in result.get("restaurants", []) if isinstance(r, dict)],
                "params": result.get("params", {})
            }
        )
        
        # Format response
        # Always use empty list instead of None to prevent NoneType errors
        restaurants = []
        if result.get("restaurants"):
            restaurants = [
                RestaurantInfo(**restaurant)
                for restaurant in result["restaurants"]
            ]
        
        return ChatResponse(
            session_id=session_id,
            message=result["message"],
            restaurants=restaurants,
            language=result["language"],
            explanation=result.get("explanation"),
            metadata=result.get("params")
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response (placeholder for future implementation).
    """
    raise HTTPException(status_code=501, detail="Streaming not implemented yet")
