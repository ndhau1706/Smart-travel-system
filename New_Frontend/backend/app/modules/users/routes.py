"""
User API routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from starlette.concurrency import run_in_threadpool
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_user_id, get_password_hash, verify_password
from app.core.deps import require_admin
from app.modules.auth.models import User, UserRole
from app.modules.users.models import UserAddress
from app.modules.users.schemas import (
    ChangePasswordRequest,
    UpdateProfileRequest,
    UpdateUserRoleRequest,
    UserAddressResponse,
    UserAddressUpsert,
)
from app.modules.auth.schemas import UserResponse
from app.shared.schemas import success_response, error_response

router = APIRouter(prefix="/users", tags=["Users"])

GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "smart-travel-images-2025")
GCS_AVATAR_PREFIX = os.environ.get("GCS_AVATAR_PREFIX", "avatars")


@router.get("/profile", response_model=dict)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Lấy thông tin thành công"
    )


@router.put("/profile", response_model=dict)
async def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    # Update fields
    if request.name is not None:
        user.name = request.name
    if request.phone is not None:
        user.phone = request.phone
    if request.avatar is not None:
        user.avatar = request.avatar
    
    await db.flush()
    await db.refresh(user)
    
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Cập nhật thông tin thành công"
    )


async def _enforce_default_address(db: AsyncSession, user_id: str) -> None:
    """Ensure there is at most one default address and at least one if any exist."""
    result = await db.execute(
        select(UserAddress)
        .where(UserAddress.user_id == user_id, UserAddress.is_default == True)  # noqa: E712
        .order_by(UserAddress.updated_at.desc(), UserAddress.created_at.desc())
    )
    defaults = result.scalars().all()
    if len(defaults) > 1:
        keep_id = defaults[0].id
        await db.execute(
            update(UserAddress)
            .where(UserAddress.user_id == user_id, UserAddress.id != keep_id)
            .values(is_default=False)
        )
        return

    if len(defaults) == 1:
        return

    result = await db.execute(
        select(UserAddress)
        .where(UserAddress.user_id == user_id)
        .order_by(UserAddress.updated_at.desc(), UserAddress.created_at.desc())
        .limit(1)
    )
    candidate = result.scalar_one_or_none()
    if candidate:
        candidate.is_default = True


@router.get("/addresses", response_model=dict)
async def list_addresses(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List current user's saved addresses."""
    result = await db.execute(
        select(UserAddress)
        .where(UserAddress.user_id == user_id)
        .order_by(UserAddress.is_default.desc(), UserAddress.updated_at.desc(), UserAddress.created_at.desc())
    )
    addresses = result.scalars().all()
    payload = [UserAddressResponse.model_validate(a).model_dump() for a in addresses]
    return success_response(data=payload, message="OK")


@router.post("/addresses", response_model=dict)
async def create_address(
    request: UserAddressUpsert,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create an address for the current user."""
    if not (request.line1 or request.city):
        return error_response("E4000", "Vui lòng nhập địa chỉ (ít nhất Line 1 hoặc Thành phố)")

    result = await db.execute(select(func.count(UserAddress.id)).where(UserAddress.user_id == user_id))
    existing_count = int(result.scalar() or 0)

    is_default = bool(request.is_default) if request.is_default is not None else False
    if existing_count == 0:
        is_default = True

    if is_default:
        await db.execute(update(UserAddress).where(UserAddress.user_id == user_id).values(is_default=False))

    address = UserAddress(
        user_id=user_id,
        label=request.label,
        line1=request.line1,
        line2=request.line2,
        city=request.city,
        latitude=request.latitude,
        longitude=request.longitude,
        is_default=is_default,
    )
    db.add(address)
    await db.flush()
    await _enforce_default_address(db, user_id)
    await db.flush()
    await db.refresh(address)

    return success_response(
        data=UserAddressResponse.model_validate(address).model_dump(),
        message="Đã thêm địa chỉ",
    )


@router.put("/addresses/{address_id}", response_model=dict)
async def update_address(
    address_id: str,
    request: UserAddressUpsert,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an address for the current user."""
    result = await db.execute(select(UserAddress).where(UserAddress.id == address_id, UserAddress.user_id == user_id))
    address = result.scalar_one_or_none()
    if not address:
        return error_response("E3004", "Không tìm thấy địa chỉ")

    fields = set(getattr(request, "model_fields_set", set()))

    next_line1 = request.line1 if "line1" in fields else address.line1
    next_city = request.city if "city" in fields else address.city
    if not (next_line1 or next_city):
        return error_response("E4000", "Vui lòng nhập địa chỉ (ít nhất Line 1 hoặc Thành phố)")

    if "label" in fields:
        address.label = request.label
    if "line1" in fields:
        address.line1 = request.line1
    if "line2" in fields:
        address.line2 = request.line2
    if "city" in fields:
        address.city = request.city
    if "latitude" in fields:
        address.latitude = request.latitude
    if "longitude" in fields:
        address.longitude = request.longitude

    if "is_default" in fields and request.is_default is not None:
        if request.is_default:
            await db.execute(
                update(UserAddress)
                .where(UserAddress.user_id == user_id, UserAddress.id != address_id)
                .values(is_default=False)
            )
            address.is_default = True
        else:
            address.is_default = False

    await db.flush()
    await _enforce_default_address(db, user_id)
    await db.flush()
    await db.refresh(address)

    return success_response(
        data=UserAddressResponse.model_validate(address).model_dump(),
        message="Đã cập nhật địa chỉ",
    )


@router.delete("/addresses/{address_id}", response_model=dict)
async def delete_address(
    address_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete an address for the current user."""
    result = await db.execute(select(UserAddress).where(UserAddress.id == address_id, UserAddress.user_id == user_id))
    address = result.scalar_one_or_none()
    if not address:
        return error_response("E3004", "Không tìm thấy địa chỉ")

    await db.delete(address)
    await db.flush()
    await _enforce_default_address(db, user_id)
    await db.flush()

    return success_response(data={"deleted": True}, message="Đã xóa địa chỉ")


@router.post("/avatar", response_model=dict)
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload user avatar image to GCS and save avatar URL"""
    if not file.content_type or not file.content_type.startswith("image/"):
        return error_response("E4000", "File không hợp lệ (chỉ hỗ trợ ảnh)")

    raw = await file.read()
    if not raw:
        return error_response("E4000", "File rỗng")
    if len(raw) > 2 * 1024 * 1024:
        return error_response("E4000", "Ảnh quá lớn (tối đa 2MB)")

    content_type = file.content_type.lower()
    ext_map = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }
    ext = ext_map.get(content_type)
    if not ext:
        return error_response("E4000", "Định dạng ảnh chưa được hỗ trợ")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")

    object_name = f"{GCS_AVATAR_PREFIX}/{user_id}/{uuid.uuid4().hex}.{ext}"

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(object_name)
        blob.cache_control = "public, max-age=31536000, immutable"
        await run_in_threadpool(blob.upload_from_string, raw, content_type=content_type)
    except Exception as e:
        return error_response("E5000", "Không upload được avatar", {"error": str(e)})

    avatar_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{object_name}"
    user.avatar = avatar_url

    await db.flush()
    await db.refresh(user)

    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Cập nhật avatar thành công",
    )


@router.put("/password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    if request.new_password != request.confirm_password:
        return error_response("E2001", "Mật khẩu xác nhận không khớp")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    if not verify_password(request.current_password, user.hashed_password):
        return error_response("E1001", "Mật khẩu hiện tại không đúng")
    
    user.hashed_password = get_password_hash(request.new_password)
    await db.flush()
    
    return success_response(
        data={"message": "Đổi mật khẩu thành công"},
        message="Đổi mật khẩu thành công"
    )


@router.get("", response_model=dict)
async def list_users(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List users (admin only)."""
    query = select(User)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()

    payload = [UserResponse.model_validate(u).model_dump() for u in users]
    return success_response(data={"users": payload, "total": total, "page": page, "limit": limit}, message="OK")


@router.put("/{target_user_id}/role", response_model=dict)
async def update_user_role(
    target_user_id: str,
    request: UpdateUserRoleRequest,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role (admin only)."""
    result = await db.execute(select(User).where(User.id == target_user_id))
    target = result.scalar_one_or_none()
    if not target:
        return error_response("E3004", "Không tìm thấy người dùng")

    target.role = UserRole(request.role.value)
    await db.flush()
    await db.refresh(target)

    return success_response(data=UserResponse.model_validate(target).model_dump(), message="Cập nhật role thành công")
