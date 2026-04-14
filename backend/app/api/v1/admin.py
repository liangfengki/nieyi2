import secrets
import string
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import verify_admin_password
from app.core.config import ADMIN_PASSWORD, ADMIN_USERNAME
from app.db.database import get_db
from app.models.models import LicenseCode, GenerationTask, UserAccount
from app.services.platform_config import (
    get_platform_api_config,
    save_platform_api_config,
    serialize_platform_api_config,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def generate_license_code() -> str:
    chars = string.ascii_uppercase + string.digits
    segments = []
    for _ in range(3):
        segment = ''.join(secrets.choice(chars) for _ in range(4))
        segments.append(segment)
    return f"NYAI-{'-'.join(segments)}"


@router.post("/login")
async def admin_login(body: dict):
    username = body.get("username", "")
    password = body.get("password", "")
    from app.core.config import ADMIN_USERNAME, ADMIN_PASSWORD
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    return {"success": True, "message": "登录成功"}


class CreateLicenseRequest(BaseModel):
    count: int = 1
    max_images: Optional[int] = None
    expires_at: Optional[str] = None
    note: Optional[str] = None


class UpdateLicenseRequest(BaseModel):
    is_active: Optional[bool] = None
    max_images: Optional[int] = None
    expires_at: Optional[str] = None
    note: Optional[str] = None


class PlatformApiConfigRequest(BaseModel):
    display_name: str
    base_url: str
    api_key: str
    model_name: str
    api_protocol: str = "OpenAI"


@router.get("/settings/platform-api")
async def get_platform_api_settings(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    config = await get_platform_api_config(db)
    return serialize_platform_api_config(config)


@router.put("/settings/platform-api")
async def update_platform_api_settings(
    body: PlatformApiConfigRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    try:
        config = await save_platform_api_config(db, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        **serialize_platform_api_config(config),
        "message": "平台免费 API 配置已保存",
    }


@router.post("/license-codes")
async def create_license_codes(
    body: CreateLicenseRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    if body.count < 1 or body.count > 50:
        raise HTTPException(status_code=400, detail="批量生成数量须在 1-50 之间")

    expires_at = None
    if body.expires_at:
        try:
            expires_at = datetime.fromisoformat(body.expires_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 ISO 格式")

    codes = []
    for _ in range(body.count):
        code = generate_license_code()
        lic = LicenseCode(
            code=code,
            max_images=body.max_images,
            expires_at=expires_at,
            note=body.note,
        )
        db.add(lic)
        codes.append(code)

    await db.commit()
    return {"codes": codes, "count": len(codes)}


@router.get("/license-codes")
async def list_license_codes(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    result = await db.execute(
        select(LicenseCode).order_by(LicenseCode.created_at.desc())
    )
    codes = result.scalars().all()
    return [
        {
            "id": c.id,
            "code": c.code,
            "max_images": c.max_images,
            "images_used": c.images_used,
            "is_active": c.is_active,
            "expires_at": c.expires_at.isoformat() if c.expires_at else None,
            "note": c.note,
            "owner_user_id": c.owner_user_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in codes
    ]


@router.put("/license-codes/{code_id}")
async def update_license_code(
    code_id: str,
    body: UpdateLicenseRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    result = await db.execute(
        select(LicenseCode).where(LicenseCode.id == code_id)
    )
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=404, detail="授权码不存在")

    if body.is_active is not None:
        lic.is_active = body.is_active
    if body.max_images is not None:
        lic.max_images = body.max_images
    if body.expires_at is not None:
        try:
            lic.expires_at = datetime.fromisoformat(body.expires_at) if body.expires_at else None
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误")
    if body.note is not None:
        lic.note = body.note

    await db.commit()
    return {"message": "授权码已更新"}


@router.delete("/license-codes/{code_id}")
async def delete_license_code(
    code_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    result = await db.execute(
        select(LicenseCode).where(LicenseCode.id == code_id)
    )
    lic = result.scalar_one_or_none()
    if not lic:
        raise HTTPException(status_code=404, detail="授权码不存在")

    await db.delete(lic)
    await db.commit()
    return {"message": "授权码已删除"}


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_admin_password),
):
    total_codes_result = await db.execute(select(func.count(LicenseCode.id)))
    total_codes = total_codes_result.scalar() or 0

    active_codes_result = await db.execute(
        select(func.count(LicenseCode.id)).where(LicenseCode.is_active == True)
    )
    active_codes = active_codes_result.scalar() or 0

    total_tasks_result = await db.execute(select(func.count(GenerationTask.id)))
    total_tasks = total_tasks_result.scalar() or 0

    completed_tasks_result = await db.execute(
        select(func.count(GenerationTask.id)).where(GenerationTask.status == "completed")
    )
    completed_tasks = completed_tasks_result.scalar() or 0

    total_users_result = await db.execute(select(func.count(UserAccount.id)))
    total_users = total_users_result.scalar() or 0

    free_users_result = await db.execute(
        select(func.count(UserAccount.id)).where(UserAccount.license_code_id.is_(None))
    )
    free_users = free_users_result.scalar() or 0

    success_rate = "0%"
    if total_tasks > 0:
        success_rate = f"{(completed_tasks / total_tasks * 100):.1f}%"

    total_images_result = await db.execute(
        select(func.coalesce(func.sum(LicenseCode.images_used), 0))
    )
    total_images = total_images_result.scalar() or 0

    return {
        "total_codes": total_codes,
        "active_codes": active_codes,
        "total_tasks": total_tasks,
        "success_rate": success_rate,
        "total_images": total_images,
        "total_users": total_users,
        "free_users": free_users,
    }
