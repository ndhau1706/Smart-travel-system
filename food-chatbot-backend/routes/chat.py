"""
Chat routes for the chatbot API.

Protected endpoints requiring JWT authentication.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from models import ChatRequest, ChatResponse, RestaurantInfo
from services import rag_pipeline, session_manager
from utils import detect_language
from middleware.auth import get_current_user, get_current_user_optional, User
import uuid

logger = logging.getLogger("chatbot.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Process a chat message and return AI response.
    
    Authentication: Optional (allows both authenticated and anonymous users)
    - Authenticated users: Full features, persistent sessions
    - Anonymous users: Limited to public sessions
    
    Args:
        request: Chat request with message and optional session_id
        current_user: Optional authenticated user
        
    Returns:
        Chat response with AI message and restaurant recommendations
    """
    try:
        # Use authenticated user's ID if available, otherwise use request.user_id
        user_id = current_user.user_id if current_user else request.user_id
        
        # Create or get session
        session_id = request.session_id
        if session_id:
            session = await session_manager.get_session(session_id)
            if not session:
                # Session doesn't exist, create new one
                session_id = None
            elif current_user and session.get('user_id') and session.get('user_id') != current_user.user_id:
                # Session belongs to different user
                logger.warning(f"User {current_user.user_id} attempted to access session {session_id}")
                raise HTTPException(status_code=403, detail="You don't have access to this session")
        
        if not session_id:
            language = detect_language(request.message)
            session_id = await session_manager.create_session(
                user_id=user_id,
                title=request.message[:50],
                language=language
            )
            logger.info(f"Created new session: {session_id} for user: {user_id}")
        
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
        
        # Process through RAG pipeline with session_id for context tracking
        logger.info(f"Processing query for session {session_id}: {request.message[:50]}...")
        result = await rag_pipeline.process(
            query=request.message,
            user_context=user_context,
            session_id=session_id
        )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error for session {request.session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response (placeholder for future implementation).
    """
    raise HTTPException(status_code=501, detail="Streaming not implemented yet")
