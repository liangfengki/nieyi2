"""
图片存储服务 — 将生成的图片保存到本地文件系统
"""
from __future__ import annotations

import os
import base64
import aiofiles
from app.core.config import GENERATED_IMAGES_DIR


async def save_image(image_data: str, task_id: str, plan_label: str, index: int) -> str:
    """
    保存图片到本地文件系统，返回相对URL路径
    image_data: base64编码的图片数据 或 data:image/xxx;base64,xxx 格式
    """
    os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

    # 去掉 data URL 前缀
    if image_data.startswith("data:"):
        # data:image/jpeg;base64,xxxxx
        header, b64_data = image_data.split(",", 1)
        if "png" in header:
            ext = "png"
        elif "webp" in header:
            ext = "webp"
        else:
            ext = "jpg"
    else:
        b64_data = image_data
        ext = "jpg"

    filename = f"{task_id}_{plan_label}_{index}.{ext}"
    filepath = os.path.join(GENERATED_IMAGES_DIR, filename)

    raw_bytes = base64.b64decode(b64_data)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(raw_bytes)

    return f"/static/generated/{filename}"


async def save_image_from_url(image_url: str, task_id: str, plan_label: str, index: int) -> str:
    """
    从URL下载图片保存到本地
    """
    import httpx

    os.makedirs(GENERATED_IMAGES_DIR, exist_ok=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(image_url)
        if response.status_code != 200:
            return image_url  # 下载失败，返回原URL

    content_type = response.headers.get("content-type", "image/jpeg")
    if "png" in content_type:
        ext = "png"
    elif "webp" in content_type:
        ext = "webp"
    else:
        ext = "jpg"

    filename = f"{task_id}_{plan_label}_{index}.{ext}"
    filepath = os.path.join(GENERATED_IMAGES_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(response.content)

    return f"/static/generated/{filename}"
