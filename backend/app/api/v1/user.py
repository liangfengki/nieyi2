import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.api.v1.auth import get_bound_license, verify_user_session
from app.db.database import get_db
from app.models.models import LicenseCode, UserAPIConfig, UserAccount

router = APIRouter(prefix="/api/v1/user", tags=["user"])


class UserAPIConfigSchema(BaseModel):
    provider_preset_id: str
    display_name: str
    model_name: str
    api_key: str
    base_url: str
    api_protocol: str = "OpenAI"
    purpose: str = "generation"


class UserAPIConfigUpdateSchema(BaseModel):
    display_name: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_protocol: Optional[str] = None
    is_active: Optional[bool] = None
    purpose: Optional[str] = None


class TestConnectionSchema(BaseModel):
    base_url: str
    api_key: str
    model_name: str
    api_protocol: str = "OpenAI"


async def require_user_license(user: UserAccount, db: AsyncSession) -> LicenseCode:
    license_obj = await get_bound_license(db, user)
    if not user.license_code_id or not license_obj:
        raise HTTPException(status_code=403, detail="请先激活授权码后再配置自己的 API")
    return license_obj


@router.get("/api-configs")
async def get_user_api_configs(
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    license_obj = await require_user_license(user, db)
    result = await db.execute(
        select(UserAPIConfig).where(UserAPIConfig.license_code_id == license_obj.id)
    )
    configs = result.scalars().all()
    return [
        {
            "id": c.id,
            "provider_preset_id": c.provider_preset_id,
            "display_name": c.display_name,
            "model_name": c.model_name,
            "api_key": c.api_key[:6] + "****" + c.api_key[-4:] if len(c.api_key) > 10 else "****",
            "base_url": c.base_url,
            "api_protocol": c.api_protocol,
            "is_active": c.is_active,
            "purpose": c.purpose,
        }
        for c in configs
    ]


@router.post("/api-configs")
async def create_user_api_config(
    body: UserAPIConfigSchema,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    license_obj = await require_user_license(user, db)
    config = UserAPIConfig(
        license_code_id=license_obj.id,
        provider_preset_id=body.provider_preset_id,
        display_name=body.display_name,
        model_name=body.model_name,
        api_key=body.api_key,
        base_url=body.base_url,
        api_protocol=body.api_protocol,
        purpose=body.purpose,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return {
        "id": config.id,
        "display_name": config.display_name,
        "model_name": config.model_name,
        "provider_preset_id": config.provider_preset_id,
        "message": "配置已保存",
    }


@router.put("/api-configs/{config_id}")
async def update_user_api_config(
    config_id: str,
    body: UserAPIConfigUpdateSchema,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    license_obj = await require_user_license(user, db)
    result = await db.execute(
        select(UserAPIConfig).where(
            UserAPIConfig.id == config_id,
            UserAPIConfig.license_code_id == license_obj.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    await db.commit()
    return {"message": "配置已更新"}


@router.delete("/api-configs/{config_id}")
async def delete_user_api_config(
    config_id: str,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    license_obj = await require_user_license(user, db)
    result = await db.execute(
        select(UserAPIConfig).where(
            UserAPIConfig.id == config_id,
            UserAPIConfig.license_code_id == license_obj.id,
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    await db.delete(config)
    await db.commit()
    return {"message": "配置已删除"}


@router.post("/test-connection")
async def test_user_connection(
    body: TestConnectionSchema,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    await require_user_license(user, db)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            if body.api_protocol == "Google API":
                url = f"{body.base_url}/models?key={body.api_key}"
                resp = await client.get(url)
            else:
                url = f"{body.base_url}/models"
                headers = {"Authorization": f"Bearer {body.api_key}"}
                resp = await client.get(url, headers=headers)

                if resp.status_code not in (200, 401, 403):
                    url = f"{body.base_url}/chat/completions"
                    resp = await client.post(
                        url,
                        headers={**headers, "Content-Type": "application/json"},
                        json={
                            "model": body.model_name,
                            "messages": [{"role": "user", "content": "hi"}],
                            "max_tokens": 5,
                        },
                    )

            if resp.status_code == 200:
                return {"success": True, "message": "连接成功！API 可用。"}
            if resp.status_code in (401, 403):
                return {"success": False, "message": "API Key 无效或权限不足"}
            if resp.status_code == 404:
                return {"success": False, "message": "API 地址错误，请检查 Base URL"}
            if resp.status_code >= 500:
                return {"success": False, "message": "API 服务端错误，可能正在维护"}
            return {"success": True, "message": f"连接成功 (状态码: {resp.status_code})"}

    except httpx.TimeoutException:
        return {"success": False, "message": "连接超时，请检查网络或 API 地址"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
