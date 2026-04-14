"""
视觉解析服务 — 调用Vision API分析产品图片，提取产品DNA
"""
from __future__ import annotations

import httpx
import base64
from .cache import compute_images_hash, get_cached_dna, cache_dna

# 内置的Vision分析提示词 — 精确提取产品结构DNA（增强版）
VISION_PROMPT = (
    "You are an expert lingerie product analyst with 20 years of experience in intimate apparel design. "
    "Your task is to examine the product image with EXTREME precision and extract EVERY structural detail "
    "for 100% faithful AI image reproduction. The generated images MUST look identical to this product.\n\n"
    
    "CRITICAL RULES:\n"
    "- You MUST identify and describe ALL details listed below. NO omissions allowed.\n"
    "- Be SPECIFIC: never use vague terms like 'standard' or 'regular'. Always describe the exact shape, size, and position.\n"
    "- If a feature is NOT present (e.g., NO straps, NO underwire, NO lace), explicitly state its absence.\n"
    "- Pay special attention to: strapless grip bands, silicone anti-slip strips, wing width, cup panel count, "
    "closure type and position, edge finishing style, fabric sheen level, and any unique design elements.\n\n"
    
    "You MUST analyze and describe ALL of the following dimensions:\n\n"
    
    "1. PRODUCT TYPE: Exact category — strapless bra, bandeau, bralette, plunge bra, balconette, "
    "full-coverage bra, sports bra, bustier, bodysuit, camisole, wireless bra, push-up bra, etc.\n\n"
    
    "2. EXACT COLOR & FINISH: Precise shade name (e.g., 'nude beige', 'blush pink', 'ivory white', 'deep black'), "
    "any color blocking or gradient, fabric sheen level (matte, satin, glossy), any contrast trim or piping color.\n\n"
    
    "3. STRAP DESIGN (CRITICAL): \n"
    "- If STRAPLESS (no shoulder straps): You MUST explicitly start this section with 'STRAPLESS DESIGN, ABSOLUTELY NO SHOULDER STRAPS'. Describe the top edge construction — is there a silicone anti-slip grip band? How wide is it? Is the top edge straight, curved, or scalloped? Describe the internal structure that provides support without straps.\n"
    "- If HAS STRAPS: describe strap width (mm estimate: skinny 3-5mm, standard 8-12mm, wide 15-25mm), "
    "strap material (same fabric, elastic, satin), attachment points (center cup, outer cup, back wing), "
    "adjustability (slider hardware visible or hidden), style (straight, racerback, halter, convertible, cross-back).\n\n"
    
    "4. CUP CONSTRUCTION: "
    "Cup style — molded seamless, seamed (specify 2-panel, 3-panel, or 4-panel), unlined sheer, padded, push-up, "
    "balconette half-cup, plunge low-center, full coverage.\n"
    "Underwire — visible underwire channeling, wireless with structured support, or soft wireless.\n"
    "Cup edge finish — scalloped lace trim, smooth bonded edge, raw-cut edge, picot elastic, satin piping.\n"
    "Center gore — wide gore, narrow gore, plunge low gore, connected/disconnected.\n\n"
    
    "5. CLOSURE SYSTEM (CRITICAL): "
    "Exact closure type and position — back hook-and-eye (specify 2-row, 3-row, or 4-row; single or double hook), "
    "front center hook-and-eye, front zipper, pull-over (no closure), side-snap, adhesive/backless, "
    "racerback J-hook clip, longline busk closure.\n"
    "If visible, describe the closure hardware color and style.\n\n"
    
    "6. BAND & WING CONSTRUCTION: "
    "Underband width — narrow (under 1cm), standard (1-2cm), wide (2-3cm), longline (3cm+).\n"
    "Side wing height — low wing, standard wing, high side-smoothing wing, extended side panel.\n"
    "Wing material — same as cup fabric, power mesh, smoothing microfiber, lace extension.\n"
    "Any boning channels, side-support slings, or structured side panels.\n\n"
    
    "7. FABRIC & TEXTURE (PRIMARY + SECONDARY): "
    "Main fabric — smooth microfiber, floral lace, geometric lace, satin, mesh, ribbed knit, cotton, "
    "seamless bonded, jacquard, velvet, tulle.\n"
    "If lace: describe the pattern (floral motif, geometric, eyelash fringe, Chantilly, Leavers lace).\n"
    "Secondary fabric/trim — mesh panels, lace overlay, satin bow, elastic edging, power mesh lining.\n"
    "Fabric weight appearance — lightweight sheer, medium weight, structured heavyweight.\n\n"
    
    "8. DECORATIVE DETAILS: "
    "Center bow (fabric type, size, position), pendant/charm, ribbon trim, embroidery pattern, "
    "logo placement, picot edge, scalloped hem, contrast stitching, rhinestone/crystal embellishment, "
    "ruching/gathering, pleating.\n\n"
    
    "9. OVERALL SHAPE & SILHOUETTE: "
    "Coverage level — full coverage, demi cup, balconette, plunge, triangle, longline.\n"
    "Neckline contour — straight across, curved sweetheart, V-plunge, asymmetrical.\n"
    "Overall aesthetic — minimalist clean, romantic lace, sporty athletic, luxury satin, everyday comfort.\n\n"
    
    "OUTPUT FORMAT:\n"
    "Output ONE dense, highly detailed English paragraph in this EXACT format:\n"
    '"a [coverage level] [exact color with sheen level] [product type] '
    "with [primary fabric + texture detail], "
    "featuring [strap design OR strapless construction with anti-slip details], "
    "[cup construction with panel count and edge finish], "
    "[closure system with row/hook count], "
    "[band width and wing construction], "
    "[decorative elements], "
    "and [overall silhouette/neckline shape]. "
    'The [secondary fabric/trim] adds [visual effect]."'
)


POSE_EXTRACTION_PROMPT = (
    "Analyze this photo and describe the MODEL'S POSE, POSTURE, and BODY POSITION in precise detail. "
    "This description will be used to generate a new image with the EXACT SAME POSE but different clothing.\n\n"
    "Focus ONLY on describing:\n"
    "1. POSE: exact body position, how arms are positioned (at sides, on hips, raised, crossed, etc), "
    "hand placement and finger position, leg stance (together, apart, one forward), foot position\n"
    "2. POSTURE: back straight/curved/leaning, shoulder position, head tilt direction and angle, "
    "chin up/down/neutral, chest position\n"
    "3. BODY ANGLE: facing camera straight on / 3/4 view / side profile / back to camera, "
    "hip tilt direction, weight distribution on legs\n"
    "4. CAMERA ANGLE: full body / half body / close-up, camera height (eye level / looking up / looking down), "
    "framing (what body parts are visible)\n"
    "5. GAZE & EXPRESSION: where the model is looking (camera / away / down / up), "
    "facial expression (confident / relaxed / serious / smiling)\n\n"
    "Output a SINGLE clear English paragraph describing ONLY the pose and position. "
    "Start with: 'The model is standing/sitting in a [pose description]...'\n"
    "Do NOT describe clothing, skin color, hair, or facial features - ONLY the pose and body position."
)

# 模特外貌分析提示词（用于参考模特模式）
MODEL_APPEARANCE_PROMPT = (
    "Analyze this photo of a person/model and describe their physical appearance in extreme detail "
    "for AI image generation. Your description will be used as a prompt to generate a new image of "
    "this SAME person, so accuracy is critical. Include ALL of the following:\n"
    "1. FACE: face shape (oval/round/angular/heart/square), exact facial structure, eyebrow shape and color, "
    "eye shape (almond/round/hooded), eye color, nose shape (button/straight/aquiline), "
    "lip shape and fullness, any distinctive features (freckles, dimples, beauty marks)\n"
    "2. HAIR: exact color (with highlights if any), length, texture (straight/wavy/curly/coily), "
    "style as shown (down/ponytail/bun/braids), hairline shape, volume\n"
    "3. SKIN: precise tone (fair porcelain/light/medium olive/tan bronze/dark/deep), undertone (warm/cool/neutral), "
    "texture quality, any visible skin features\n"
    "4. BODY: overall build (slim/petite/athletic/average/curvy/voluptuous/plus-size), approximate proportions, "
    "shoulder width relative to hips, waist definition, overall body silhouette\n"
    "5. OVERALL: approximate age range (20s/30s/etc), ethnicity appearance as perceived from photo, "
    "overall vibe (natural/athletic/glamorous/editorial), distinguishing characteristics\n\n"
    "Output a SINGLE dense, specific English paragraph starting with: "
    '"A [age-range] [ethnicity-appearance] female with [face-shape] face, '
    "Be extremely specific and concrete — another AI must be able to recreate this exact person from your words alone. "
    "Do NOT use vague terms like 'attractive' or 'average'. Instead use specific descriptors."
)

FALLBACK_DNA = (
    "a form-fitting undergarment with smooth fabric texture, featuring structured design "
    "and body-contouring silhouette"
)

FALLBACK_MODEL_DESC = (
    "The model is standing in a natural relaxed pose, facing the camera with arms resting at sides, "
    "weight evenly distributed on both legs, shoulders back, chin slightly raised."
)


def _is_google_direct(base_url: str) -> bool:
    return "googleapis.com" in base_url or "generativelanguage" in base_url


async def extract_product_dna(
    base64_images: list[str],
    api_config,
) -> str:
    """
    调用Vision API分析产品图片，返回英文产品DNA描述（带缓存）
    支持: Gemini Vision / OpenAI Vision 协议
    """
    image_hash = compute_images_hash(base64_images)
    cached = get_cached_dna(image_hash)
    if cached:
        return cached

    base_url = api_config.base_url.rstrip("/") if api_config.base_url else ""
    model_name = api_config.model_name
    api_key = api_config.api_key

    # 清洗URL
    if base_url.endswith("/chat/completions"):
        base_url = base_url[:-17]

    # 判断是否直连 Google API
    is_google_direct = "googleapis.com" in base_url or "generativelanguage" in base_url

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 对于 Gemini 生图模型，用同族文本模型做视觉分析
    vision_model = model_name
    if "image-preview" in vision_model:
        vision_model = vision_model.replace("-image-preview", "")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Gemini 直连 Google API
        if "gemini" in model_name.lower() and is_google_direct:
            clean_base = base_url.replace("/v1", "")
            req_url = f"{clean_base}/v1beta/models/{vision_model}:generateContent"
            parts = [{"text": VISION_PROMPT}]
            for b64 in base64_images[:3]:
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64,
                    }
                })

            payload = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"maxOutputTokens": 600},
            }
            response = await client.post(req_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    pass

        # OpenAI Vision 协议 (中转站 / 非 Gemini 模型)
        else:
            clean_base = base_url
            if not clean_base.endswith("/v1"):
                clean_base = clean_base + "/v1"
            req_url = f"{clean_base}/chat/completions"
            content = [{"type": "text", "text": VISION_PROMPT}]
            for b64 in base64_images[:3]:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                })

            payload = {
                "model": vision_model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 600,
            }
            print(f"[Vision] Calling {req_url} model={vision_model}")
            response = await client.post(req_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                try:
                    return data["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    pass
            else:
                print(f"[Vision] API error: {response.status_code} {response.text[:200]}")

    # 如果API调用失败，返回通用描述
    print(f"[Vision] API call failed (status={response.status_code}), using fallback DNA")
    return (
        "a structured undergarment with smooth bonded fabric, featuring standard back hook-and-eye closure, "
        "molded cups with smooth finish, adjustable straps, and a clean minimalist silhouette"
    )


async def extract_pose_dna(
    base64_image: str,
    api_config,
) -> str:
    """
    调用Vision API分析模特图片，提取纯粹的姿势动作描述（不含外貌/服装）
    """
    image_hash = compute_images_hash([base64_image]) + "_pose"
    cached = get_cached_dna(image_hash)
    if cached:
        return cached

    base_url = api_config.base_url.rstrip("/") if api_config.base_url else ""
    model_name = api_config.model_name
    api_key = api_config.api_key

    if base_url.endswith("/chat/completions"):
        base_url = base_url[:-17]

    is_google_direct = "googleapis.com" in base_url or "generativelanguage" in base_url

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    vision_model = model_name
    if "image-preview" in vision_model:
        vision_model = vision_model.replace("-image-preview", "")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Gemini 直连 Google API
        if "gemini" in model_name.lower() and is_google_direct:
            clean_base = base_url.replace("/v1", "")
            req_url = f"{clean_base}/v1beta/models/{vision_model}:generateContent"
            parts = [{"text": POSE_EXTRACTION_PROMPT}]
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_image,
                }
            })

            payload = {
                "contents": [{"role": "user", "parts": parts}],
                "generationConfig": {"maxOutputTokens": 300},
            }
            response = await client.post(req_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                try:
                    result = data["candidates"][0]["content"]["parts"][0]["text"]
                    cache_dna(image_hash, result)
                    return result
                except (KeyError, IndexError):
                    pass

        # OpenAI Vision 协议 (中转站)
        else:
            clean_base = base_url
            if not clean_base.endswith("/v1"):
                clean_base = clean_base + "/v1"
            req_url = f"{clean_base}/chat/completions"
            content = [{"type": "text", "text": POSE_EXTRACTION_PROMPT}]
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            })

            payload = {
                "model": vision_model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 300,
            }
            print(f"[Vision - Pose] Calling {req_url} model={vision_model}")
            response = await client.post(req_url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                try:
                    result = data["choices"][0]["message"]["content"]
                    cache_dna(image_hash, result)
                    return result
                except (KeyError, IndexError):
                    pass
            else:
                print(f"[Vision - Pose] API error: {response.status_code} {response.text[:200]}")

    print(f"[Vision - Pose] API call failed, using fallback pose")
    return "The model is standing naturally facing the camera, with arms relaxed by her sides and shoulders squared."


async def extract_model_description(
    model_base64: str,
    api_config,
) -> str:
    """
    调用Vision API分析参考模特照片，返回详细的外貌描述
    用于替代通用的persona描述，实现"按照参考模特生图"
    """
    base_url = api_config.base_url.rstrip("/") if api_config.base_url else ""
    model_name = api_config.model_name
    api_key = api_config.api_key

    if base_url.endswith("/chat/completions"):
        base_url = base_url[:-17]

    is_google = _is_google_direct(base_url)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 保持原始模型名，不要修改
    vision_model = model_name

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if "gemini" in model_name.lower() and is_google:
                clean_base = base_url.replace("/v1", "")
                req_url = f"{clean_base}/v1beta/models/{vision_model}:generateContent"
                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": MODEL_APPEARANCE_PROMPT},
                                {
                                    "inline_data": {
                                        "mime_type": "image/jpeg",
                                        "data": model_base64,
                                    }
                                },
                            ],
                        }
                    ],
                    "generationConfig": {"maxOutputTokens": 500},
                }
                response = await client.post(req_url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    try:
                        return data["candidates"][0]["content"]["parts"][0]["text"]
                    except (KeyError, IndexError):
                        print("[ModelVision] Failed to parse Gemini direct response")
                else:
                    print(f"[ModelVision] Gemini direct error: {response.status_code}")
            else:
                clean_base = base_url
                if not clean_base.endswith("/v1"):
                    clean_base = clean_base + "/v1"
                req_url = f"{clean_base}/chat/completions"
                payload = {
                    "model": vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": MODEL_APPEARANCE_PROMPT},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{model_base64}"
                                    },
                                },
                            ],
                        }
                    ],
                    "max_tokens": 500,
                }
                print(f"[ModelVision] Calling {req_url} model={vision_model}")
                response = await client.post(req_url, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    try:
                        return data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError):
                        print("[ModelVision] Failed to parse OpenAI response")
                else:
                    print(
                        f"[ModelVision] API error: {response.status_code} {response.text[:200]}"
                    )

    except httpx.TimeoutException:
        print("[ModelVision] Request timed out")
    except httpx.ConnectError as e:
        print(f"[ModelVision] Connection error: {e}")
    except Exception as e:
        print(f"[ModelVision] Unexpected error: {e}")

    print("[ModelVision] Failed, using generic fallback")
    return FALLBACK_MODEL_DESC