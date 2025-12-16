"""
Session management routes.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from models import (
    SessionCreate,
    SessionInfo,
    SessionListResponse,
    SessionHistoryResponse,
    MessageInfo
)
from services import session_manager

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/", response_model=SessionInfo)
async def create_session(request: SessionCreate):
    """
    Create a new chat session.
    
    Args:
        request: Session creation request
        
    Returns:
        Created session information
    """
    try:
        session_id = await session_manager.create_session(
            user_id=request.user_id,
            title=request.title,
            language=request.language
        )
        
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=500, detail="Failed to create session")
        
        return SessionInfo(**session, message_count=0)
        
    except Exception as e:
        print(f"Create session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=SessionListResponse)
async def list_sessions(user_id: Optional[str] = None, limit: int = 50):
    """
    List all sessions, optionally filtered by user.
    
    Args:
        user_id: Optional user ID filter
        limit: Maximum number of sessions to return
        
    Returns:
        List of sessions
    """
    try:
        sessions = await session_manager.list_sessions(user_id=user_id, limit=limit)
        
        session_infos = [SessionInfo(**session) for session in sessions]
        
        return SessionListResponse(
            sessions=session_infos,
            total=len(session_infos)
        )
        
    except Exception as e:
        print(f"List sessions error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """
    Get a session with its message history.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session information with messages
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
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
        print(f"Get session history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and all its messages.
    
    Args:
        session_id: Session ID
        
    Returns:
        Success message
    """
    try:
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        await session_manager.delete_session(session_id)
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete session error: {e}")
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
        print(f"Update session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
