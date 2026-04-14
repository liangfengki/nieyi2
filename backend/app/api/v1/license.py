from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime, timezone
from app.db.database import get_db
from app.models.models import LicenseCode
from app.api.v1.auth import verify_license_code

router = APIRouter(prefix="/api/v1/license", tags=["license"])


class ValidateRequest(BaseModel):
    code: str


@router.post("/validate")
async def validate_license(req: ValidateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LicenseCode).where(LicenseCode.code == req.code)
    )
    lic = result.scalar_one_or_none()

    if not lic:
        raise HTTPException(status_code=401, detail="授权码无效")

    if not lic.is_active:
        raise HTTPException(status_code=403, detail="授权码已被吊销")

    if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="授权码已过期")

    remaining = None
    if lic.max_images is not None:
        remaining = max(0, lic.max_images - lic.images_used)
        if remaining <= 0:
            raise HTTPException(status_code=403, detail="授权码配额已用完")

    return {
        "valid": True,
        "code": lic.code,
        "max_images": lic.max_images,
        "images_used": lic.images_used,
        "remaining": remaining,
        "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        "note": lic.note,
    }


@router.get("/info")
async def get_license_info(lic: LicenseCode = Depends(verify_license_code)):
    remaining = None
    if lic.max_images is not None:
        remaining = max(0, lic.max_images - lic.images_used)

    return {
        "code": lic.code,
        "max_images": lic.max_images,
        "images_used": lic.images_used,
        "remaining": remaining,
        "is_active": lic.is_active,
        "expires_at": lic.expires_at.isoformat() if lic.expires_at else None,
        "note": lic.note,
        "created_at": lic.created_at.isoformat() if lic.created_at else None,
    }
