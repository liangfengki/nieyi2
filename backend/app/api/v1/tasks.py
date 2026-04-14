from __future__ import annotations

import asyncio
import base64
import json
import re
from dataclasses import dataclass
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import ensure_license_active, get_bound_license, verify_user_session
from app.db.database import AsyncSessionLocal, get_db
from app.models.models import GenerationTask, LicenseCode, UserAPIConfig, UserAccount
from app.prompts.personas import PERSONAS
from app.prompts.service import assemble_prompt, get_shot_template
from app.services.cleanup import cleanup_old_generation_tasks
from app.services.platform_config import RuntimeAPIConfig, get_platform_api_config
from app.services.storage import save_image, save_image_from_url
from app.services.vision import extract_model_description, extract_pose_dna, extract_product_dna

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    images: list[str] = []
    plan_results: list[dict] = []
    product_dna: Optional[str] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class HistoryResponse(BaseModel):
    tasks: list[TaskStatusResponse]
    total: int


@dataclass
class GenerationAccessContext:
    mode: str
    license_obj: Optional[LicenseCode]
    generation_configs: list[UserAPIConfig | RuntimeAPIConfig]
    vision_config: UserAPIConfig | RuntimeAPIConfig


async def _get_owned_task_filters(db: AsyncSession, user: UserAccount):
    filters = [GenerationTask.user_id == user.id]
    license_obj = await get_bound_license(db, user)
    if license_obj:
        filters.append(GenerationTask.license_code_id == license_obj.id)
    return filters


async def _resolve_generation_access(
    db: AsyncSession,
    user: UserAccount,
    model_id: Optional[str],
) -> GenerationAccessContext:
    license_obj = await get_bound_license(db, user)
    if license_obj:
        license_obj = ensure_license_active(license_obj, require_quota=False)

        result = await db.execute(
            select(UserAPIConfig).where(
                UserAPIConfig.license_code_id == license_obj.id,
                UserAPIConfig.is_active == True,
                UserAPIConfig.purpose == "generation",
            )
        )
        generation_configs = result.scalars().all()

        if not generation_configs:
            fallback_result = await db.execute(
                select(UserAPIConfig).where(
                    UserAPIConfig.license_code_id == license_obj.id,
                    UserAPIConfig.is_active == True,
                )
            )
            generation_configs = fallback_result.scalars().all()

        if model_id:
            for config in generation_configs:
                if config.id == model_id or config.provider_preset_id == model_id:
                    generation_configs = [config]
                    break

        if not generation_configs:
            raise HTTPException(status_code=400, detail="当前账号已激活授权码，但尚未配置可用的 API Key")

        vision_result = await db.execute(
            select(UserAPIConfig).where(
                UserAPIConfig.license_code_id == license_obj.id,
                UserAPIConfig.is_active == True,
                UserAPIConfig.purpose == "vision",
            )
        )
        vision_config = vision_result.scalars().first() or generation_configs[0]

        return GenerationAccessContext(
            mode="license",
            license_obj=license_obj,
            generation_configs=generation_configs,
            vision_config=vision_config,
        )

    free_limit = user.free_generations_limit or 0
    free_used = user.free_generations_used or 0
    if free_used >= free_limit:
        raise HTTPException(
            status_code=403,
            detail="免费生成次数已用完，请先激活授权码并配置您自己的 API 后继续使用",
        )

    platform_config = await get_platform_api_config(db)
    if not platform_config:
        raise HTTPException(
            status_code=503,
            detail="平台免费 API 尚未配置，请联系管理员后再试",
        )

    return GenerationAccessContext(
        mode="free",
        license_obj=None,
        generation_configs=[platform_config],
        vision_config=platform_config,
    )


@router.get("/history", response_model=HistoryResponse)
async def get_task_history(
    limit: int = 50,
    offset: int = 0,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的生成历史"""
    from sqlalchemy import func as sa_func

    owner_filters = await _get_owned_task_filters(db, user)

    count_result = await db.execute(
        select(sa_func.count()).select_from(GenerationTask).where(
            or_(*owner_filters),
            GenerationTask.status.in_(["completed", "failed"]),
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(GenerationTask)
        .where(
            or_(*owner_filters),
            GenerationTask.status.in_(["completed", "failed"]),
        )
        .order_by(GenerationTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    tasks = result.scalars().all()

    return HistoryResponse(
        tasks=[
            TaskStatusResponse(
                task_id=task.id,
                status=task.status,
                images=task.images if task.images else [],
                plan_results=task.plan_results if task.plan_results else [],
                product_dna=task.product_dna,
                error_message=task.error_message,
                created_at=task.created_at.isoformat() if task.created_at else None,
            )
            for task in tasks
        ],
        total=total,
    )


@router.post("/generate", response_model=TaskResponse)
async def create_generate_task(
    mannequin_images: List[UploadFile] = File(...),
    model_image: UploadFile = File(None),
    product_3d_image: UploadFile = File(None),
    persona_id: str = Form("european_natural"),
    selected_plans: str = Form(...),
    text_level: str = Form("no_text"),
    bust_type: str = Form("natural"),
    skin_tone: str = Form("light"),
    custom_prompt: Optional[str] = Form(None),
    model_id: Optional[str] = Form(None),
    model_mode: str = Form("ai_generate"),
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    """提交图片生成任务（邮箱会话模式）"""
    try:
        plans = json.loads(selected_plans)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="selected_plans 格式错误，需要 JSON 数组")

    if not plans:
        raise HTTPException(status_code=400, detail="请至少选择一个生图方案")

    num_images = len(plans)
    access = await _resolve_generation_access(db, user, model_id)

    if access.mode == "license" and access.license_obj:
        license_obj = access.license_obj
        if license_obj.max_images is not None and (license_obj.images_used + num_images) > license_obj.max_images:
            remaining = max(0, license_obj.max_images - license_obj.images_used)
            raise HTTPException(
                status_code=403,
                detail=f"授权码配额不足：剩余 {remaining} 张，本次需要 {num_images} 张",
            )

    base64_images: list[str] = []
    for image in mannequin_images:
        content = await image.read()
        base64_images.append(base64.b64encode(content).decode("utf-8"))

    model_base64 = None
    if model_image:
        content = await model_image.read()
        model_base64 = base64.b64encode(content).decode("utf-8")

    product_3d_base64 = None
    if product_3d_image:
        content = await product_3d_image.read()
        product_3d_base64 = base64.b64encode(content).decode("utf-8")

    cost_per_image = 0.7
    total_cost = cost_per_image * num_images

    if model_base64 and any(plan.get("shot_type") == "pose_reference" for plan in plans):
        model_mode = "reference_model"

    task = GenerationTask(
        user_id=user.id,
        license_code_id=access.license_obj.id if access.license_obj else None,
        market=",".join(sorted(set(plan.get("shot_type", plan.get("market", "custom")) for plan in plans))),
        status="processing",
        model_name=access.generation_configs[0].model_name,
        cost=total_cost,
        images=[],
        persona_id=persona_id,
        selected_plans=plans,
        model_mode=model_mode,
    )
    db.add(task)

    if access.mode == "license" and access.license_obj:
        access.license_obj.images_used += num_images
    else:
        user.free_generations_used = (user.free_generations_used or 0) + 1

    await db.commit()
    await db.refresh(task)

    asyncio.create_task(
        run_ai_generation_workflow(
            task_id=task.id,
            plans=plans,
            persona_id=persona_id,
            text_level=text_level,
            bust_type=bust_type,
            skin_tone=skin_tone,
            model_mode=model_mode,
            custom_prompt=custom_prompt,
            base64_images=base64_images,
            model_base64=model_base64,
            product_3d_base64=product_3d_base64,
            gen_configs=access.generation_configs,
            vision_config=access.vision_config,
        )
    )

    message = f"任务已提交，将生成 {num_images} 张图片"
    if access.mode == "free":
        message += "（本次已消耗 1 次免费生成次数）"

    return TaskResponse(task_id=task.id, status="processing", message=message)


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    user: UserAccount = Depends(verify_user_session),
    db: AsyncSession = Depends(get_db),
):
    """轮询获取当前用户任务状态"""
    owner_filters = await _get_owned_task_filters(db, user)

    result = await db.execute(
        select(GenerationTask).where(
            GenerationTask.id == task_id,
            or_(*owner_filters),
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        images=task.images if task.images else [],
        plan_results=task.plan_results if task.plan_results else [],
        product_dna=task.product_dna,
        error_message=task.error_message,
        created_at=task.created_at.isoformat() if task.created_at else None,
    )


# ---------------------------------------------------------------------------
# 以下为后台工作流，保持原有核心逻辑，仅配置来源改为“平台免费 API / 用户 API”通用对象
# ---------------------------------------------------------------------------


async def run_ai_generation_workflow(
    task_id: str,
    plans: list[dict],
    persona_id: str,
    text_level: str,
    bust_type: str,
    skin_tone: str,
    model_mode: str,
    custom_prompt: str | None,
    base64_images: list[str],
    model_base64: str | None,
    product_3d_base64: str | None,
    gen_configs: list,
    vision_config,
):
    try:
        dna_source_images = base64_images
        if product_3d_base64:
            dna_source_images = [product_3d_base64] + base64_images
            print(f"[Task {task_id}] Step 1: Extracting Product DNA from 3D reference image...")
        else:
            print(f"[Task {task_id}] Step 1: Extracting Product DNA...")

        has_pose_reference = any(plan.get("shot_type") == "pose_reference" for plan in plans)

        vision_tasks = [extract_product_dna(dna_source_images, vision_config)]

        if has_pose_reference and model_base64:
            print(f"[Task {task_id}] Step 1.5: Extracting Pose DNA from model reference image...")
            vision_tasks.append(extract_pose_dna(model_base64, vision_config))
        else:
            vision_tasks.append(asyncio.sleep(0))

        if model_mode == "reference_model" and model_base64:
            print(f"[Task {task_id}] Step 2: Reference model mode — analyzing model photo...")
            vision_tasks.append(extract_model_description(model_base64, vision_config))
        else:
            vision_tasks.append(asyncio.sleep(0))

        print(f"[Task {task_id}] Running vision extraction tasks concurrently...")
        vision_results = await asyncio.gather(*vision_tasks, return_exceptions=False)

        product_dna = vision_results[0]
        pose_dna = vision_results[1] if has_pose_reference and model_base64 else None
        model_description = vision_results[2] if model_mode == "reference_model" and model_base64 else None

        print(f"[Task {task_id}] Product DNA: {product_dna[:100]}...")
        if pose_dna:
            print(f"[Task {task_id}] Pose DNA: {pose_dna[:100]}...")

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.product_dna = product_dna
                await db.commit()

        persona = PERSONAS.get(persona_id)
        persona_prompt = persona["prompt"] if persona else None

        if model_mode == "reference_model" and model_base64:
            persona_prompt = model_description
            print(f"[Task {task_id}] Model description: {model_description[:150]}...")
        else:
            print(f"[Task {task_id}] Step 2: AI generate mode — Persona = {persona_id}")

        generated_urls: list[str] = []
        plan_results: list[dict] = []

        if product_3d_base64:
            print(f"[Task {task_id}] Using 3D product reference as primary image")

        plan_tasks = []
        for index, plan_spec in enumerate(plans):
            shot_type_id = plan_spec.get("shot_type")
            if not shot_type_id:
                print(f"[Task {task_id}] Legacy plan format: {plan_spec}, skipping")
                continue

            template = get_shot_template(shot_type_id)
            if not template:
                print(f"[Task {task_id}] Template not found for {plan_spec}, skipping")
                continue

            final_prompt = assemble_prompt(
                prompt_template=template["prompt_template"],
                product_dna=product_dna,
                persona_prompt=persona_prompt if template.get("needs_persona") else None,
                text_level=text_level,
                bust_type=bust_type,
                skin_tone=skin_tone,
                model_mode=model_mode if model_base64 else "ai_generate",
                custom_prompt=custom_prompt,
                shot_type_id=shot_type_id,
                pose_dna=pose_dna,
            )

            api_config = gen_configs[index % len(gen_configs)]

            images_for_plan: list[str] = []
            if shot_type_id == "pose_reference" and model_base64:
                images_for_plan.append(model_base64)
                if product_3d_base64:
                    images_for_plan.append(product_3d_base64)
                images_for_plan.extend(base64_images)
            elif model_mode == "reference_model" and model_base64:
                if product_3d_base64:
                    images_for_plan.append(product_3d_base64)
                images_for_plan.extend(base64_images)
                images_for_plan.append(model_base64)
            else:
                if product_3d_base64:
                    images_for_plan.append(product_3d_base64)
                images_for_plan.extend(base64_images)

            plan_tasks.append(
                {
                    "index": index,
                    "plan_spec": plan_spec,
                    "shot_type_id": shot_type_id,
                    "template": template,
                    "prompt": final_prompt,
                    "api_config": api_config,
                    "images": images_for_plan,
                }
            )

        print(
            f"[Task {task_id}] Step 3: Generating {len(plan_tasks)} images concurrently with {len(gen_configs)} API keys..."
        )

        coroutines = [
            generate_single_image(
                task_id=task_id,
                plan_task=plan_task,
            )
            for plan_task in plan_tasks
        ]
        results = await asyncio.gather(*coroutines, return_exceptions=True)

        for index, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[Task {task_id}] Image {index + 1} failed with exception: {result}")
                continue

            if result and result.get("image_url"):
                generated_urls.append(result["image_url"])
                plan_results.append(
                    {
                        "shot_type": result["shot_type_id"],
                        "shot_name": result["shot_name"],
                        "image_url": result["image_url"],
                    }
                )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                if generated_urls:
                    task.status = "completed"
                    task.images = generated_urls
                    task.plan_results = plan_results
                else:
                    task.status = "failed"
                    task.error_message = f"所有 {len(plans)} 张图片生成失败，请检查 API 配置或稍后重试"
                await db.commit()

        asyncio.create_task(cleanup_old_generation_tasks(100))
        print(f"[Task {task_id}] Done. Generated {len(generated_urls)}/{len(plans)} images.")

    except Exception as exc:
        print(f"[Task {task_id}] Workflow error: {exc}")
        import traceback

        traceback.print_exc()
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(GenerationTask).where(GenerationTask.id == task_id))
            task = result.scalar_one_or_none()
            if task:
                task.status = "failed"
                task.error_message = str(exc)
                await db.commit()


async def generate_single_image(
    task_id: str,
    plan_task: dict,
) -> dict | None:
    i = plan_task["index"]
    shot_type_id = plan_task["shot_type_id"]
    template = plan_task["template"]
    final_prompt = plan_task["prompt"]
    api_config = plan_task["api_config"]
    all_images = plan_task["images"]
    plan_display = template["name"]

    print(f"[Task {task_id}] Generating image {i + 1}: {plan_display} (Config: {api_config.display_name})")

    if not api_config.base_url:
        print(f"[Task {task_id}] Image {i + 1} SKIPPED: API config '{api_config.display_name}' has no base_url")
        return None

    base_url = api_config.base_url.rstrip("/")
    if base_url.endswith("/chat/completions"):
        base_url = base_url[:-17]

    headers = {
        "Authorization": f"Bearer {api_config.api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        image_url = None
        for gen_attempt in range(3):
            image_url = await call_image_api(
                client=client,
                prompt=final_prompt,
                base64_images=all_images,
                base_url=base_url,
                headers=headers,
                gen_config=api_config,
                task_id=task_id,
            )
            if image_url:
                break
            if gen_attempt < 2:
                wait = 10 * (gen_attempt + 1)
                print(f"[Task {task_id}] Image {i + 1} failed, retrying in {wait}s... (attempt {gen_attempt + 2}/3)")
                await asyncio.sleep(wait)

        if image_url:
            if image_url.startswith("data:") or not image_url.startswith("http"):
                local_url = await save_image(image_url, task_id, shot_type_id, i)
            elif image_url.startswith("http"):
                local_url = await save_image_from_url(image_url, task_id, shot_type_id, i)
            else:
                local_url = image_url
        else:
            local_url = None
            print(f"[Task {task_id}] Image {i + 1} ({plan_display}) FAILED after 3 attempts")

        if local_url:
            return {
                "shot_type_id": shot_type_id,
                "shot_name": plan_display,
                "image_url": local_url,
            }

    return None


def _is_google_direct(base_url: str) -> bool:
    return "googleapis.com" in base_url or "generativelanguage" in base_url


def _extract_image_from_markdown(content: str) -> str | None:
    match = re.search(r'!\[.*?\]\((data:image/[^)]+)\)', content)
    if match:
        return match.group(1)
    match = re.search(r'(data:image/\S+;base64,[A-Za-z0-9+/=]+)', content)
    if match:
        return match.group(1)
    return None


async def call_image_api(
    client: httpx.AsyncClient,
    prompt: str,
    base64_images: list[str],
    base_url: str,
    headers: dict,
    gen_config,
    task_id: str,
) -> str | None:
    model_name = gen_config.model_name

    try:
        if "gemini" in model_name.lower() and not _is_google_direct(base_url):
            clean_base = base_url.rstrip("/")
            if clean_base.endswith("/chat/completions"):
                clean_base = clean_base[:-17]
            if not clean_base.endswith("/v1"):
                clean_base = clean_base + "/v1"
            req_url = f"{clean_base}/chat/completions"

            user_content = [{"type": "text", "text": prompt}]
            images_to_send = base64_images[:6]
            is_pose_reference = "POSE REFERENCE" in prompt

            for idx, b64 in enumerate(images_to_send):
                if is_pose_reference:
                    if idx == 0:
                        user_content.append({"type": "text", "text": "[IMAGE BELOW: POSE REFERENCE - COPY POSE ONLY, DO NOT COPY ITS LINGERIE]"})
                    elif idx == 1:
                        user_content.append({"type": "text", "text": "[IMAGE BELOW: PRODUCT REFERENCE - COPY LINGERIE FROM HERE]"})

                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    }
                )

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": user_content}],
                "max_tokens": 4096,
            }

            print(f"[Task {task_id}] Calling proxy: {req_url} model={model_name}")

            response = None
            for attempt in range(5):
                response = await client.post(req_url, headers=headers, json=payload)
                if response.status_code == 429:
                    wait_time = 10 * (attempt + 1)
                    print(f"[Task {task_id}] Rate limited (429), waiting {wait_time}s... (attempt {attempt + 1}/5)")
                    await asyncio.sleep(wait_time)
                    continue
                break

            if response and response.status_code == 200:
                data = response.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                    if isinstance(content, str):
                        image_data = _extract_image_from_markdown(content)
                        if image_data:
                            return image_data
                        print(f"[Task {task_id}] No image found in response (len={len(content)})")
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "image_url":
                                return part["image_url"]["url"]
                except (KeyError, IndexError) as exc:
                    print(f"[Task {task_id}] Failed to parse proxy response: {exc}")
            else:
                err_text = response.text[:500] if response else "No response"
                print(f"[Task {task_id}] Proxy API error: {response.status_code if response else 'N/A'} {err_text}")
            return None

        if "gemini" in model_name.lower():
            clean_base = base_url.replace("/v1", "")
            req_url = f"{clean_base}/v1beta/models/{model_name}:generateContent"

            parts = [{"text": prompt}]
            if base64_images:
                images_to_send = base64_images[:6]
                is_pose_reference = "POSE REFERENCE" in prompt

                for idx, b64 in enumerate(images_to_send):
                    if is_pose_reference:
                        if idx == 0:
                            parts.append({"text": "[IMAGE BELOW: POSE REFERENCE - COPY POSE ONLY, DO NOT COPY ITS LINGERIE]"})
                        elif idx == 1:
                            parts.append({"text": "[IMAGE BELOW: PRODUCT REFERENCE - COPY LINGERIE FROM HERE]"})

                    parts.append(
                        {
                            "inline_data": {"mime_type": "image/jpeg", "data": b64},
                        }
                    )

            payload = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {},
                "responseModalities": ["IMAGE"],
                "imageConfig": {},
            }

            for attempt in range(3):
                response = await client.post(req_url, headers=headers, json=payload)
                if response.status_code == 429:
                    print(f"[Task {task_id}] Rate limited, waiting 5s... (attempt {attempt + 1}/3)")
                    await asyncio.sleep(5)
                    continue
                break

            if response.status_code == 200:
                data = response.json()
                try:
                    b64_res = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                    return f"data:image/jpeg;base64,{b64_res}"
                except (KeyError, IndexError):
                    print(f"[Task {task_id}] Failed to parse Gemini response: {data}")
            else:
                print(f"[Task {task_id}] Gemini API error: {response.status_code} {response.text[:200]}")
            return None

        if "seedream" in model_name.lower():
            payload = {
                "model": model_name,
                "prompt": prompt,
                "n": 1,
                "size": "1024*1024",
                "extra_body": {
                    "watermark": False,
                    "sequential_image_generation": "disabled",
                },
            }
            req_url = f"{base_url}/images/generations"

            for attempt in range(3):
                response = await client.post(req_url, headers=headers, json=payload)
                if response.status_code == 429:
                    await asyncio.sleep(5)
                    continue
                break

            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    item = data["data"][0]
                    if "url" in item:
                        return item["url"]
                    if "b64_json" in item:
                        return f"data:image/png;base64,{item['b64_json']}"
            else:
                print(f"[Task {task_id}] Seedream API error: {response.status_code}")
            return None

        payload = {
            "model": model_name,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        }
        req_url = f"{base_url}/images/generations"

        for attempt in range(3):
            response = await client.post(req_url, headers=headers, json=payload)
            if response.status_code == 429:
                await asyncio.sleep(5)
                continue
            break

        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                item = data["data"][0]
                if "url" in item:
                    return item["url"]
                if "b64_json" in item:
                    return f"data:image/png;base64,{item['b64_json']}"
        else:
            print(f"[Task {task_id}] OpenAI API error: {response.status_code} {response.text[:200]}")
        return None

    except Exception as exc:
        print(f"[Task {task_id}] Image generation error: {exc}")
        return None
