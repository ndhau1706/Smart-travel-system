"""
Common FastAPI dependencies (auth + authorization)
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.modules.auth.models import User, UserRole


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get the current authenticated user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


def require_roles(*roles: UserRole):
    """Require current user to have one of provided roles."""

    async def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _dep


require_admin = require_roles(UserRole.ADMIN)
require_restaurant_owner = require_roles(UserRole.RESTAURANT_OWNER)
require_admin_or_owner = require_roles(UserRole.ADMIN, UserRole.RESTAURANT_OWNER)

