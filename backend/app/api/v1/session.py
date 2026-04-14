from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import (
    build_user_session_payload,
    ensure_license_active,
    ensure_utc_datetime,
    generate_session_token,
    get_bound_license,
    get_client_ip,
    get_license_by_code,
    normalize_email,
    verify_user_session,
)
from app.core.config import (
    EMAIL_LOGIN_CODE_TTL_MINUTES,
    EMAIL_LOGIN_DEBUG,
    EMAIL_LOGIN_MAX_SENDS_PER_HOUR,
    EMAIL_LOGIN_MAX_VERIFY_ATTEMPTS,
    EMAIL_LOGIN_RESEND_COOLDOWN_SECONDS,
    PLATFORM_FREE_GENERATIONS,
)
from app.db.database import get_db
from app.models.models import EmailLoginCode, UserAccount
from app.services.email_auth import email_login_available, send_login_code_email

router = APIRouter(prefix="/api/v1/session", tags=["session"])


class EmailCodeRequest(BaseModel):
    email: EmailStr


class VerifyEmailCodeRequest(BaseModel):
    email: EmailStr
    code: str


class ActivateLicenseRequest(BaseModel):
    code: str


class EmailCodeRequestResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: int
    resend_in_seconds: int
    debug_code: Optional[str] = None



def _generate_email_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"



def _hash_email_code(email: str, code: str) -> str:
    normalized_email = normalize_email(email)
    normalized_code = (code or "").strip()
    payload = f"{normalized_email}:{normalized_code}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@router.post("/request-email-code", response_model=EmailCodeRequestResponse)
async def request_email_code(
    body: EmailCodeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    if not email_login_available():
        raise HTTPException(status_code=503, detail="邮箱登录暂未启用，请先配置 SMTP 发信服务")

    email = normalize_email(body.email)
    client_ip = get_client_ip(request)
    now = datetime.now(timezone.utc)
    resend_at = now + timedelta(seconds=EMAIL_LOGIN_RESEND_COOLDOWN_SECONDS)
    expires_at = now + timedelta(minutes=EMAIL_LOGIN_CODE_TTL_MINUTES)

    result = await db.execute(select(EmailLoginCode).where(EmailLoginCode.email == email))
    login_code = result.scalar_one_or_none()

    last_sent_at = ensure_utc_datetime(login_code.last_sent_at) if login_code else None
    if last_sent_at:
        retry_after = int((last_sent_at + timedelta(seconds=EMAIL_LOGIN_RESEND_COOLDOWN_SECONDS) - now).total_seconds())
        if retry_after > 0:
            raise HTTPException(status_code=429, detail=f"验证码已发送，请在 {retry_after} 秒后重试")

    send_count = 0
    if login_code:
        if last_sent_at and last_sent_at >= now - timedelta(hours=1):
            send_count = login_code.send_count or 0
        if send_count >= EMAIL_LOGIN_MAX_SENDS_PER_HOUR:
            raise HTTPException(status_code=429, detail="验证码发送过于频繁，请 1 小时后再试")

    raw_code = _generate_email_code()
    code_hash = _hash_email_code(email, raw_code)

    if login_code:
        login_code.code_hash = code_hash
        login_code.expires_at = expires_at
        login_code.last_sent_at = now
        login_code.send_count = send_count + 1
        login_code.verify_attempts = 0
        login_code.request_ip = client_ip
        login_code.consumed_at = None
    else:
        login_code = EmailLoginCode(
            email=email,
            code_hash=code_hash,
            expires_at=expires_at,
            last_sent_at=now,
            send_count=1,
            verify_attempts=0,
            request_ip=client_ip,
            consumed_at=None,
        )
        db.add(login_code)

    try:
        await db.flush()
        await send_login_code_email(email, raw_code)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        raise

    await db.commit()

    message = "验证码已发送，请查收邮箱"
    if EMAIL_LOGIN_DEBUG:
        message = "验证码已生成；如未配置 SMTP，可直接使用下方开发验证码登录"

    return EmailCodeRequestResponse(
        success=True,
        message=message,
        expires_in_seconds=max(0, int((expires_at - now).total_seconds())),
        resend_in_seconds=max(0, int((resend_at - now).total_seconds())),
        debug_code=raw_code if EMAIL_LOGIN_DEBUG else None,
    )


@router.post("/verify-email-code")
async def verify_email_code(
    body: VerifyEmailCodeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email = normalize_email(body.email)
    code = (body.code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="请输入验证码")

    result = await db.execute(select(EmailLoginCode).where(EmailLoginCode.email == email))
    login_code = result.scalar_one_or_none()
    if not login_code:
        raise HTTPException(status_code=400, detail="请先获取验证码")

    now = datetime.now(timezone.utc)
    consumed_at = ensure_utc_datetime(login_code.consumed_at)
    expires_at = ensure_utc_datetime(login_code.expires_at)
    if consumed_at:
        raise HTTPException(status_code=400, detail="验证码已使用，请重新获取")
    if expires_at and expires_at < now:
        raise HTTPException(status_code=400, detail="验证码已过期，请重新获取")
    if (login_code.verify_attempts or 0) >= EMAIL_LOGIN_MAX_VERIFY_ATTEMPTS:
        raise HTTPException(status_code=429, detail="验证码错误次数过多，请重新获取")

    expected_hash = _hash_email_code(email, code)
    if login_code.code_hash != expected_hash:
        login_code.verify_attempts = (login_code.verify_attempts or 0) + 1
        await db.commit()
        remaining = max(0, EMAIL_LOGIN_MAX_VERIFY_ATTEMPTS - login_code.verify_attempts)
        if remaining == 0:
            raise HTTPException(status_code=429, detail="验证码错误次数过多，请重新获取")
        raise HTTPException(status_code=400, detail=f"验证码错误，还可再试 {remaining} 次")

    login_code.consumed_at = now

    user_result = await db.execute(select(UserAccount).where(UserAccount.email == email))
    user = user_result.scalar_one_or_none()
    if user:
        user.session_token = generate_session_token()
        user.last_login_at = now
        if not user.free_generations_limit:
            user.free_generations_limit = PLATFORM_FREE_GENERATIONS
    else:
        user = UserAccount(
            email=email,
            session_token=generate_session_token(),
            registered_ip=get_client_ip(request),
            free_generations_limit=PLATFORM_FREE_GENERATIONS,
            free_generations_used=0,
            last_login_at=now,
        )
        db.add(user)
        await db.flush()

    await db.commit()
    if not user.id:
        await db.refresh(user)

    license_obj = await get_bound_license(db, user)
    return build_user_session_payload(user, license_obj)


@router.get("/me")
async def get_session_me(
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    license_obj = await get_bound_license(db, user)
    return build_user_session_payload(user, license_obj)


@router.post("/activate-license")
async def activate_license(
    body: ActivateLicenseRequest,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    code = (body.code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="请输入授权码")

    license_obj = await get_license_by_code(db, code)
    ensure_license_active(license_obj, require_quota=False)

    if user.license_code_id and user.license_code_id != license_obj.id:
        raise HTTPException(status_code=409, detail="当前邮箱已绑定其他授权码，如需更换请联系管理员")

    if license_obj.owner_user_id and license_obj.owner_user_id != user.id:
        raise HTTPException(status_code=403, detail="该授权码已绑定其他邮箱账号")

    license_obj.owner_user_id = user.id
    user.license_code_id = license_obj.id
    user.last_login_at = datetime.now(timezone.utc)

    await db.commit()
    return build_user_session_payload(user, license_obj)
