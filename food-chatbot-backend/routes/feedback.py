"""
Feedback routes.
"""
from fastapi import APIRouter, HTTPException
from models import FeedbackRequest, FeedbackResponse
from services import feedback_service

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback.
    
    Args:
        request: Feedback request
        
    Returns:
        Success response
    """
    try:
        feedback_id = await feedback_service.save_feedback(
            session_id=request.session_id,
            feedback_type=request.feedback_type,
            rating=request.rating,
            comment=request.comment,
            message_id=request.message_id,
            restaurant_id=request.restaurant_id
        )
        
        return FeedbackResponse(
            success=True,
            message=f"Feedback saved successfully (ID: {feedback_id})"
        )
        
    except Exception as e:
        print(f"Submit feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/restaurant/{restaurant_id}")
async def get_restaurant_feedback(restaurant_id: int):
    """
    Get feedback statistics for a restaurant.
    
    Args:
        restaurant_id: Restaurant ID
        
    Returns:
        Feedback statistics
    """
    try:
        stats = await feedback_service.get_restaurant_feedback_stats(restaurant_id)
        return stats
        
    except Exception as e:
        print(f"Get restaurant feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session_feedback(session_id: str):
    """
    Get all feedback for a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        List of feedback entries
    """
    try:
        feedback = await feedback_service.get_session_feedback(session_id)
        return {"feedback": feedback}
        
    except Exception as e:
        print(f"Get session feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
