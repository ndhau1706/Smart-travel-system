"""
Session management routes.

Protected endpoints requiring JWT authentication.
Implements IDOR protection - users can only access their own sessions.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models import (
    SessionCreate,
    SessionInfo,
    SessionListResponse,
    SessionHistoryResponse,
    MessageInfo
)
from services import session_manager
from middleware.auth import get_current_user, get_current_user_optional, User

logger = logging.getLogger("chatbot.sessions")

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionInfo)
async def create_session(
    request: SessionCreate,
    current_user: User = Depends(get_current_user_optional)
):
    """
    Create a new chat session.
    
    Args:
        request: Session creation request
        current_user: Optional authenticated user
        
    Returns:
        Created session information
    """
    try:
        # Use authenticated user's ID if available
        user_id = current_user.user_id if current_user else request.user_id
        
        session_id = await session_manager.create_session(
            user_id=user_id,
            title=request.title,
            language=request.language
        )
        
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        logger.info(f"Session created: {session_id} for user: {user_id}")
        return SessionInfo(**session, message_count=0)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=SessionListResponse)
async def list_sessions(
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    List all sessions for the authenticated user.
    
    IDOR Protection: Users can only see their own sessions.
    
    Args:
        current_user: Authenticated user (required)
        limit: Maximum number of sessions to return
        
    Returns:
        List of user's sessions
    """
    try:
        # Only return sessions belonging to the authenticated user
        sessions = await session_manager.list_sessions(
            user_id=current_user.user_id, 
            limit=limit
        )
        
        session_infos = [SessionInfo(**session) for session in sessions]
        
        logger.info(f"Listed {len(session_infos)} sessions for user: {current_user.user_id}")
        return SessionListResponse(
            sessions=session_infos,
            total=len(session_infos)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List sessions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a session with its message history.
    
    IDOR Protection: Users can only access their own sessions.
    Requires JWT authentication.
    
    Security:
    - Verifies session ownership before returning data
    - Prevents unauthorized access to other users' sessions
    - Protection against brute force and session enumeration
    
    Args:
        session_id: Session ID
        current_user: Authenticated user (required)
        
    Returns:
        Session information with messages (only if authorized)
        
    Raises:
        400: Invalid session_id format
        401: Not authenticated
        403: Session belongs to different user
        404: Session not found
    """
    # Basic validation: session_id should be non-empty string
    if not session_id or not isinstance(session_id, str):
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # IDOR Protection: Verify session ownership
        session_user_id = session.get('user_id')
        
        if session_user_id is not None and session_user_id != current_user.user_id:
            logger.warning(f"IDOR attempt: User {current_user.user_id} tried to access session {session_id}")
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this session"
            )
        
        messages = await session_manager.get_messages(session_id)
        
        message_infos = [MessageInfo(**msg) for msg in messages]
        session['message_count'] = len(messages)
        
        return SessionHistoryResponse(
            session=SessionInfo(**session),
            messages=message_infos
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user_id: Optional[str] = None
):
    """
    Delete a session and all its messages.
    
    BUG #25 FIX: Added authorization check to prevent unauthorized deletion.
    
    Args:
        session_id: Session ID
        user_id: User ID for authorization
        
    Returns:
        Success message
        
    Raises:
        400: Invalid session_id format
        401: Unauthorized
        404: Session not found
    """
    # Basic validation: session_id should be non-empty string
    if not session_id or not isinstance(session_id, str):
        raise HTTPException(status_code=400, detail="Invalid session_id format")
    
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # BUG #25 FIX: Authorization check before deletion
        session_user_id = session.get('user_id')
        
        if session_user_id is not None:
            if user_id is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required. Please provide user_id."
                )
            
            if session_user_id != user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: You cannot delete this session"
                )
        
        await session_manager.delete_session(session_id)
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}")
async def update_session(session_id: str, title: str):
    """
    Update session title.
    
    Args:
        session_id: Session ID
        title: New title
        
    Returns:
        Updated session information
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await session_manager.update_session(session_id, title=title)
        
        updated_session = await session_manager.get_session(session_id)
        messages = await session_manager.get_messages(session_id)
        updated_session['message_count'] = len(messages)
        
        return SessionInfo(**updated_session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
