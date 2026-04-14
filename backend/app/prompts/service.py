"""
提示词组装服务
负责：返回策略列表、组装最终提示词
"""
from __future__ import annotations

from app.prompts.personas import PERSONAS
from app.prompts.markets import (
    SHOT_TYPES,
    TEXT_LEVELS,
    BUST_TYPES,
    SKIN_TONES,
    _REF_PREFIX,
    _MODEL_REF_PREFIX,
    _MODEL_APPEARANCE_REF_PREFIX,
)


def get_available_strategies() -> dict:
    """返回所有可用的拍摄类型、模特设定、文字等级，供前端渲染选择器"""
    shot_types_out = {}
    for st_id, st in SHOT_TYPES.items():
        shot_types_out[st_id] = {
            "id": st["id"],
            "name": st["name"],
            "name_en": st["name_en"],
            "description": st["description"],
            "icon": st.get("icon", "image"),
            "category": st.get("category", "other"),
            "needs_persona": st["needs_persona"],
            "aspect_ratio": st["aspect_ratio"],
        }

    personas_out = {}
    for pid, persona in PERSONAS.items():
        personas_out[pid] = {
            "id": persona["id"],
            "name": persona["name"],
            "name_en": persona["name_en"],
            "description": persona["description"],
            "suitable_markets": persona.get("suitable_markets", []),
        }

    text_levels_out = {}
    for tl_id, tl in TEXT_LEVELS.items():
        text_levels_out[tl_id] = {
            "id": tl["id"],
            "name": tl["name"],
            "name_en": tl["name_en"],
            "description": tl["description"],
        }

    bust_types_out = {}
    for bt_id, bt in BUST_TYPES.items():
        bust_types_out[bt_id] = {
            "id": bt["id"],
            "name": bt["name"],
            "name_en": bt["name_en"],
            "description": bt["description"],
        }

    skin_tones_out = {}
    for st_id, st in SKIN_TONES.items():
        skin_tones_out[st_id] = {
            "id": st["id"],
            "name": st["name"],
            "name_en": st["name_en"],
            "description": st["description"],
        }

    return {
        "shot_types": shot_types_out,
        "personas": personas_out,
        "text_levels": text_levels_out,
        "bust_types": bust_types_out,
        "skin_tones": skin_tones_out,
    }


def get_shot_template(shot_type_id: str) -> dict | None:
    """获取指定拍摄类型的完整模板配置"""
    return SHOT_TYPES.get(shot_type_id)


def get_text_level_instruction(text_level_id: str) -> str:
    """获取文字等级的具体指令"""
    level = TEXT_LEVELS.get(text_level_id)
    if level:
        return level["instruction"]
    # 默认：无文字
    return TEXT_LEVELS["no_text"]["instruction"]


def get_bust_prompt(bust_type_id: str) -> str:
    """获取胸型描述提示词"""
    bt = BUST_TYPES.get(bust_type_id)
    return bt["prompt"] if bt else ""


def get_skin_tone_prompt(skin_tone_id: str) -> str:
    """获取肤色描述提示词"""
    st = SKIN_TONES.get(skin_tone_id)
    return st["prompt"] if st else ""


def assemble_prompt(
    prompt_template: str,
    product_dna: str,
    persona_prompt: str | None = None,
    text_level: str = "no_text",
    bust_type: str = "natural",
    skin_tone: str = "light",
    model_mode: str = "ai_generate",
    custom_prompt: str | None = None,
    shot_type_id: str | None = None,
    pose_dna: str | None = None,
) -> str:
    """
    将模板中的占位符替换为实际值
    model_mode: "ai_generate" = AI根据人设生成, "reference_model" = 参照用户上传的模特图姿势
    shot_type_id: 拍摄类型ID，用于判断是否需要展示脸部
    """
    result = prompt_template

    # 判断是否需要展示脸部的拍摄类型
    show_face_shots = {"model_front", "lifestyle_scene"}
    should_show_face = shot_type_id in show_face_shots

    # 参考模特模式（非姿势参考）：替换前缀，保留模特外貌+下装，只替换内衣
    if model_mode == "reference_model" and shot_type_id != "pose_reference":
        # 替换 _REF_PREFIX 为 _MODEL_APPEARANCE_REF_PREFIX
        if _REF_PREFIX in result:
            result = result.replace(_REF_PREFIX, _MODEL_APPEARANCE_REF_PREFIX)

    # 替换产品 DNA
    result = result.replace("[FIXED_PRODUCT_DNA]", product_dna)

    # 替换姿势DNA (如果存在)
    if "[FIXED_POSE_DNA]" in result:
        result = result.replace("[FIXED_POSE_DNA]", pose_dna if pose_dna else "Standard natural standing pose.")

    # 替换人设/姿势描述
    if persona_prompt:
        # AI 自由生成模式 或 参考模特模式：注入人设 + 胸型 + 肤色
        enhanced_persona = persona_prompt
        bust_desc = get_bust_prompt(bust_type)
        skin_desc = get_skin_tone_prompt(skin_tone)
        extras = ", ".join(filter(None, [bust_desc, skin_desc]))
        if extras:
            enhanced_persona = f"{enhanced_persona}, {extras}"
            
        # Add negative constraints if product is strapless
        if "STRAPLESS DESIGN" in product_dna.upper() or "NO SHOULDER STRAPS" in product_dna.upper():
            enhanced_persona += " [CRITICAL: The model is wearing a STRAPLESS top. Ensure bare shoulders, bare collarbone area, and absolutely NO straps are drawn on the shoulders or chest.]"

        result = result.replace("[FIXED_MODEL_PERSONA]", enhanced_persona)
    else:
        # Even if no persona, we still need to enforce strapless constraint if applicable
        if "STRAPLESS DESIGN" in product_dna.upper() or "NO SHOULDER STRAPS" in product_dna.upper():
            result = result.replace("[FIXED_MODEL_PERSONA]", "[CRITICAL: The model is wearing a STRAPLESS top. Ensure bare shoulders, bare collarbone area, and absolutely NO straps are drawn on the shoulders or chest.]")
        else:
            result = result.replace("[FIXED_MODEL_PERSONA]", "")

    # 注入文字等级
    text_instruction = get_text_level_instruction(text_level)
    result = result.replace("[TEXT_INSTRUCTION]", text_instruction)

    # 参考模特模式的额外处理
    if model_mode == "reference_model" and shot_type_id != "pose_reference":
        # 移除"不显示脸"的矛盾描述（参考模式需要展示脸部以匹配参考模特）
        if should_show_face:
            for face_hide in [
                "face not fully visible, ",
                "face not fully visible",
                "face not visible, ",
                "face not visible",
                "Face not visible in any view. ",
                "Face not visible in any view.",
            ]:
                result = result.replace(face_hide, "")

        # 替换"Paired with matching color underwear bottoms"为保留参考模特下装的指令
        result = result.replace(
            "Paired with matching color underwear bottoms.",
            "Keep the pants/bottoms IDENTICAL to the reference model photo."
        )

    if custom_prompt:
        result = result.rstrip()
        # 在 --ar 前插入自定义提示词
        for ar_tag in ["--ar 3:4", "--ar 16:9", "Aspect ratio 16:9"]:
            if result.endswith(ar_tag):
                result = result[: -len(ar_tag)].rstrip() + f" {custom_prompt} {ar_tag}"
                break
        else:
            result += f" {custom_prompt}"

    return result
