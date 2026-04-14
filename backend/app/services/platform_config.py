from dataclasses import dataclass, asdict
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import (
    PLATFORM_API_BASE_URL,
    PLATFORM_API_DISPLAY_NAME,
    PLATFORM_API_KEY,
    PLATFORM_API_MODEL_NAME,
    PLATFORM_API_PROTOCOL,
)
from app.models.models import SystemSetting

PLATFORM_API_SETTING_KEY = "platform_api_config"


@dataclass
class RuntimeAPIConfig:
    display_name: str
    base_url: str
    api_key: str
    model_name: str
    api_protocol: str = "OpenAI"
    source: str = "database"


def _build_runtime_config(data: dict, source: str) -> Optional[RuntimeAPIConfig]:
    base_url = (data.get("base_url") or "").strip()
    api_key = (data.get("api_key") or "").strip()
    model_name = (data.get("model_name") or "").strip()
    if not base_url or not api_key or not model_name:
        return None

    return RuntimeAPIConfig(
        display_name=(data.get("display_name") or PLATFORM_API_DISPLAY_NAME).strip(),
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
        api_protocol=(data.get("api_protocol") or PLATFORM_API_PROTOCOL).strip() or "OpenAI",
        source=source,
    )


def get_env_platform_api_config() -> Optional[RuntimeAPIConfig]:
    return _build_runtime_config(
        {
            "display_name": PLATFORM_API_DISPLAY_NAME,
            "base_url": PLATFORM_API_BASE_URL,
            "api_key": PLATFORM_API_KEY,
            "model_name": PLATFORM_API_MODEL_NAME,
            "api_protocol": PLATFORM_API_PROTOCOL,
        },
        source="env",
    )


async def get_platform_api_config(db: AsyncSession) -> Optional[RuntimeAPIConfig]:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == PLATFORM_API_SETTING_KEY)
    )
    setting = result.scalar_one_or_none()
    if setting and isinstance(setting.value, dict):
        runtime = _build_runtime_config(setting.value, source="database")
        if runtime:
            return runtime

    return get_env_platform_api_config()


async def save_platform_api_config(db: AsyncSession, data: dict) -> RuntimeAPIConfig:
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == PLATFORM_API_SETTING_KEY)
    )
    setting = result.scalar_one_or_none()

    payload = {
        "display_name": (data.get("display_name") or PLATFORM_API_DISPLAY_NAME).strip(),
        "base_url": (data.get("base_url") or "").strip(),
        "api_key": (data.get("api_key") or "").strip(),
        "model_name": (data.get("model_name") or "").strip(),
        "api_protocol": (data.get("api_protocol") or PLATFORM_API_PROTOCOL).strip() or "OpenAI",
    }

    runtime = _build_runtime_config(payload, source="database")
    if not runtime:
        raise ValueError("平台免费 API 配置不完整，请填写 Base URL、API Key 和模型名")

    if setting:
        setting.value = payload
    else:
        setting = SystemSetting(key=PLATFORM_API_SETTING_KEY, value=payload)
        db.add(setting)

    await db.commit()
    return runtime


def serialize_platform_api_config(config: Optional[RuntimeAPIConfig]) -> dict:
    if not config:
        return {
            "display_name": PLATFORM_API_DISPLAY_NAME,
            "base_url": PLATFORM_API_BASE_URL,
            "api_key": "",
            "model_name": PLATFORM_API_MODEL_NAME,
            "api_protocol": PLATFORM_API_PROTOCOL,
            "configured": False,
            "source": None,
        }

    data = asdict(config)
    data["configured"] = True
    return data
