"""
Base schemas for API responses
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List
from datetime import datetime

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ApiMeta(BaseModel):
    timestamp: datetime = datetime.utcnow()
    request_id: Optional[str] = None
    pagination: Optional[PaginationMeta] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str
    error: Optional[ApiError] = None
    meta: Optional[ApiMeta] = None
    
    class Config:
        from_attributes = True


def success_response(data: T, message: str = "Success") -> dict:
    """Create a success response"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "error": None,
        "meta": {
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def error_response(code: str, message: str, details: dict = None) -> dict:
    """Create an error response"""
    return {
        "success": False,
        "data": None,
        "message": message,
        "error": {
            "code": code,
            "message": message,
            "details": details
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def paginated_response(
    data: List[T],
    total: int,
    page: int,
    limit: int,
    message: str = "Success"
) -> dict:
    """Create a paginated response"""
    total_pages = (total + limit - 1) // limit
    return {
        "success": True,
        "data": data,
        "message": message,
        "error": None,
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    }
