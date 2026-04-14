from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, Header, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME, PLATFORM_FREE_GENERATIONS
from app.db.database import get_db
from app.models.models import LicenseCode, UserAccount


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def ensure_utc_datetime(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def generate_session_token() -> str:
    return uuid4().hex


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def verify_admin_password(x_admin_password: str = Header(...)):
    if x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="管理员密码错误")


async def get_license_by_code(db: AsyncSession, code: str) -> Optional[LicenseCode]:
    result = await db.execute(select(LicenseCode).where(LicenseCode.code == code))
    return result.scalar_one_or_none()


async def get_bound_license(db: AsyncSession, user: UserAccount) -> Optional[LicenseCode]:
    if not user.license_code_id:
        return None
    result = await db.execute(select(LicenseCode).where(LicenseCode.id == user.license_code_id))
    return result.scalar_one_or_none()


async def verify_license_code(
    x_license_code: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> LicenseCode:
    license_obj = await get_license_by_code(db, x_license_code)
    return ensure_license_active(license_obj)


async def verify_user_session(
    x_user_session: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> UserAccount:
    result = await db.execute(
        select(UserAccount).where(UserAccount.session_token == x_user_session)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="登录状态已失效，请重新输入邮箱登录")
    return user


async def get_optional_user_session(
    x_user_session: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[UserAccount]:
    if not x_user_session:
        return None
    result = await db.execute(
        select(UserAccount).where(UserAccount.session_token == x_user_session)
    )
    return result.scalar_one_or_none()


def ensure_license_active(license_obj: Optional[LicenseCode], require_quota: bool = True) -> LicenseCode:
    if not license_obj:
        raise HTTPException(status_code=401, detail="授权码无效")

    now = datetime.now(timezone.utc)
    expires_at = ensure_utc_datetime(license_obj.expires_at)
    if not license_obj.is_active:
        raise HTTPException(status_code=403, detail="授权码已被吊销")
    if expires_at and expires_at < now:
        raise HTTPException(status_code=403, detail="授权码已过期")
    if require_quota and license_obj.max_images is not None and license_obj.images_used >= license_obj.max_images:
        raise HTTPException(status_code=403, detail="授权码配额已用完")

    return license_obj


def _license_status(license_obj: LicenseCode) -> str:
    now = datetime.now(timezone.utc)
    expires_at = ensure_utc_datetime(license_obj.expires_at)
    if not license_obj.is_active:
        return "inactive"
    if expires_at and expires_at < now:
        return "expired"
    if license_obj.max_images is not None and license_obj.images_used >= license_obj.max_images:
        return "quota_exhausted"
    return "active"


def build_user_session_payload(user: UserAccount, license_obj: Optional[LicenseCode] = None) -> dict:
    free_limit = user.free_generations_limit or PLATFORM_FREE_GENERATIONS
    free_used = user.free_generations_used or 0
    free_remaining = max(0, free_limit - free_used)

    license_payload = None
    has_active_license = False
    if license_obj:
        status = _license_status(license_obj)
        has_active_license = status == "active"
        remaining = None
        if license_obj.max_images is not None:
            remaining = max(0, license_obj.max_images - license_obj.images_used)
        license_payload = {
            "code": license_obj.code,
            "max_images": license_obj.max_images,
            "images_used": license_obj.images_used,
            "remaining": remaining,
            "expires_at": license_obj.expires_at.isoformat() if license_obj.expires_at else None,
            "note": license_obj.note,
            "status": status,
        }

    return {
        "session_token": user.session_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "registered_ip": user.registered_ip,
            "free_generations_limit": free_limit,
            "free_generations_used": free_used,
            "free_remaining": free_remaining,
            "has_active_license": has_active_license,
            "license_bound": bool(user.license_code_id),
        },
        "license": license_payload,
    }
