"""
Feedback routes.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from models import FeedbackRequest, FeedbackResponse
from services import feedback_service
from middleware.auth import get_current_user_optional, get_current_user, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Submit user feedback.
    
    Supports both authenticated and anonymous feedback.
    Authenticated users get their feedback linked to their account.
    
    Args:
        request: Feedback request containing session_id, rating, comment, etc.
        current_user: Optional authenticated user
        
    Returns:
        Success response with feedback ID
        
    Raises:
        500: Internal server error if feedback cannot be saved
    """
    try:
        user_id = current_user.user_id if current_user else None
        
        feedback_id = await feedback_service.save_feedback(
            session_id=request.session_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            comment=request.comment,
            message_id=request.message_id,
            restaurant_id=request.restaurant_id,
            user_id=user_id
        )
        
        logger.info(f"Feedback submitted: ID={feedback_id}, user={user_id}, session={request.session_id}")
        
        return FeedbackResponse(
            success=True,
            message=f"Feedback saved successfully (ID: {feedback_id})"
        )
        
    except Exception as e:
        logger.error(f"Submit feedback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/restaurant/{restaurant_id}")
async def get_restaurant_feedback(restaurant_id: int):
    """
    Get feedback statistics for a restaurant.
    
    This is a public endpoint - no authentication required.
    Used for displaying restaurant ratings and reviews.
    
    Args:
        restaurant_id: Restaurant ID
        
    Returns:
        Feedback statistics including average rating, count, and comments
        
    Raises:
        404: Restaurant not found
        500: Internal server error
    """
    try:
        stats = await feedback_service.get_restaurant_feedback_stats(restaurant_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Restaurant not found or no feedback available")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get restaurant feedback error for ID={restaurant_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_feedback(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all feedback for a session.
    
    IDOR Protection: Users can only access feedback for their own sessions.
    Requires JWT authentication.
    
    Args:
        session_id: Session ID
        current_user: Authenticated user (required)
        
    Returns:
        List of feedback entries for the session
        
    Raises:
        401: Not authenticated
        403: Session belongs to different user
        500: Internal server error
    """
    try:
        # Import session manager for ownership check
        from services.session_manager import session_manager
        
        # Verify session ownership
        session = await session_manager.get_session(session_id)
        if session:
            session_user_id = session.get('user_id')
            if session_user_id and session_user_id != current_user.user_id:
                logger.warning(f"IDOR attempt: User {current_user.user_id} tried to access feedback for session {session_id}")
                raise HTTPException(
                    status_code=403,
                    detail="You don't have access to this session's feedback"
                )
        
        feedback = await feedback_service.get_session_feedback(session_id)
        return {"feedback": feedback}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session feedback error for session={session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
