"""
User feedback service.
"""
from typing import Optional
import aiosqlite
from database import db_manager


class FeedbackService:
    """Manages user feedback and ratings."""
    
    async def save_feedback(
        self,
        session_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        message_id: Optional[int] = None,
        restaurant_id: Optional[int] = None
    ) -> int:
        """
        Save user feedback.
        
        Args:
            session_id: Session ID
            feedback_type: Type of feedback (positive/negative/neutral)
            rating: Rating (1-5)
            comment: User comment
            message_id: Related message ID
            restaurant_id: Related restaurant ID
            
        Returns:
            Feedback ID
        """
        async with db_manager.get_connection() as db:
            cursor = await db.execute("""
                INSERT INTO user_feedback
                (session_id, message_id, restaurant_id, feedback_type, rating, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, message_id, restaurant_id, feedback_type, rating, comment))
            
            feedback_id = cursor.lastrowid
            await db.commit()
            
            return feedback_id
    
    async def get_restaurant_feedback_stats(self, restaurant_id: int) -> dict:
        """
        Get feedback statistics for a restaurant.
        
        Args:
            restaurant_id: Restaurant ID
            
        Returns:
            Feedback statistics
        """
        async with db_manager.get_connection() as db:
            # Get average user rating
            async with db.execute("""
                SELECT AVG(rating) as avg_rating, COUNT(*) as count
                FROM user_feedback
                WHERE restaurant_id = ? AND rating IS NOT NULL
            """, (restaurant_id,)) as cursor:
                row = await cursor.fetchone()
                avg_rating = row[0] if row[0] else 0
                rating_count = row[1]
            
            # Get feedback type distribution
            async with db.execute("""
                SELECT feedback_type, COUNT(*) as count
                FROM user_feedback
                WHERE restaurant_id = ?
                GROUP BY feedback_type
            """, (restaurant_id,)) as cursor:
                rows = await cursor.fetchall()
                feedback_dist = {row[0]: row[1] for row in rows}
            
            return {
                "average_rating": avg_rating,
                "rating_count": rating_count,
                "feedback_distribution": feedback_dist
            }
    
    async def get_session_feedback(self, session_id: str) -> list:
        """
        Get all feedback for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of feedback entries
        """
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM user_feedback
                WHERE session_id = ?
                ORDER BY created_at DESC
            """, (session_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


# Global instance
feedback_service = FeedbackService()
