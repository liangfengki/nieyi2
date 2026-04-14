"""
拍摄类型提示词库 (Shot Types)
按视图类型组织，替代原有的市场策略体系。
每个提示词都包含 IMAGE REFERENCE REQUIREMENT 确保保留内衣细节。
"""

# ============================================================
# 图片文字等级控制
# ============================================================
TEXT_LEVELS = {
    "no_text": {
        "id": "no_text",
        "name": "无文字",
        "name_en": "Clean (No Text)",
        "description": "纯净画面，不含任何文字、箭头或图形覆盖",
        "instruction": "Pure clean image without any text, graphics, arrows, or overlays.",
    },
    "minimal_text": {
        "id": "minimal_text",
        "name": "少量标注",
        "name_en": "Minimal Labels",
        "description": "少量产品特征标注，细线指示关键设计点",
        "instruction": (
            "Add minimal text labels with thin leader lines pointing to 2-3 key design features "
            "of the product. Keep text small and elegant."
        ),
    },
    "rich_text": {
        "id": "rich_text",
        "name": "丰富信息图",
        "name_en": "Rich Infographic",
        "description": "电商风格信息图：粗体标题、虚线箭头、画中画对比、功能标注",
        "instruction": (
            "Add rich infographic elements: bold text headings, dashed technical lines with inward "
            "arrows highlighting key features, picture-in-picture comparison panels showing before/after "
            "or detail close-ups, and feature callout labels. E-commerce listing ready."
        ),
    },
}

# ============================================================
# 胸型设置
# ============================================================
BUST_TYPES = {
    "natural": {
        "id": "natural",
        "name": "自然",
        "name_en": "Natural",
        "description": "自然胸型，不做特殊强调",
        "prompt": "",
    },
    "full_round": {
        "id": "full_round",
        "name": "饱满圆润",
        "name_en": "Full & Round",
        "description": "饱满圆润C杯，丰盈有型，自然挺拔",
        "prompt": "with full, rounded C-cup bust showing natural volume, smooth contours, and uplifted shape",
    },
    "plump": {
        "id": "plump",
        "name": "丰满性感",
        "name_en": "Plump & Voluptuous",
        "description": "丰满D杯，曲线突出，性感丰盈",
        "prompt": "with plump, voluptuous D-cup bust with prominent curves, natural cleavage, and full rounded shape",
    },
    "petite": {
        "id": "petite",
        "name": "小巧精致",
        "name_en": "Petite & Elegant",
        "description": "精致A/B杯，纤细优雅",
        "prompt": "with petite, delicate A/B-cup bust with elegant slim silhouette and refined proportions",
    },
}

# ============================================================
# 肤色设置
# ============================================================
SKIN_TONES = {
    "fair": {
        "id": "fair",
        "name": "白皙",
        "name_en": "Fair",
        "description": "白皙透亮，瓷器般的肤质",
        "prompt": "fair porcelain skin with rosy undertone and flawless complexion",
    },
    "light": {
        "id": "light",
        "name": "自然肤色",
        "name_en": "Light Natural",
        "description": "自然健康的浅肤色，温暖基调",
        "prompt": "natural light skin with healthy warm undertone",
    },
    "medium": {
        "id": "medium",
        "name": "小麦色",
        "name_en": "Medium / Olive",
        "description": "健康小麦色/橄榄色肤色",
        "prompt": "warm olive medium skin tone with sun-kissed healthy glow",
    },
    "tan": {
        "id": "tan",
        "name": "古铜色",
        "name_en": "Tan / Bronze",
        "description": "古铜色健康运动肤色",
        "prompt": "golden bronze tan skin with warm radiant athletic glow",
    },
    "dark": {
        "id": "dark",
        "name": "深色",
        "name_en": "Dark / Ebony",
        "description": "深色/巧克力色肤色，光泽细腻",
        "prompt": "rich deep dark skin with luminous smooth complexion and natural sheen",
    },
}

# ============================================================
# 核心提示词前缀 — 确保保留内衣细节
# ============================================================
_REF_PREFIX = (
    "[IMAGE REFERENCE REQUIREMENT: Strictly replicate the exact structural design, color, pattern, "
    "and every detail of the provided reference image of the product]. "
)

# 参考模特模式前缀 — 1:1还原参考模特，只替换内衣为3D图款式
_MODEL_REF_PREFIX = (
    "[CRITICAL INSTRUCTION - FULL MODEL REFERENCE + LINGERIE SWAP]: "
    "Reference Image 1 (FIRST image): A FULL MODEL REFERENCE photo. You MUST replicate the EXACT SAME PERSON — "
    "same face, skin tone, body type, hair, AND the EXACT SAME POSE — same body position, arm placement, "
    "hand position, leg stance, body angle, and camera framing. "
    "CRITICAL: Keep EVERYTHING from this reference model EXACTLY THE SAME — face, hair, skin, body, pants/bottoms, "
    "shoes, accessories, background, lighting. The ONLY thing you must change is the LINGERIE TOP/BRA. "
    "Reference Images 2+ (REMAINING images): The NEW LINGERIE PRODUCT to be worn INSTEAD of the original. "
    "STRICTLY replicate the exact structural design, color, pattern, straps, closure, lace details, "
    "and every detail of this NEW product. Do NOT change the new product design. "
    "TASK: Generate the EXACT SAME model in the EXACT SAME pose, wearing the NEW LINGERIE from images 2+ "
    "instead of the original. Everything else must remain IDENTICAL to image 1. "
)

# 参考模特外貌模式前缀 — 保留模特外貌+下装，只替换内衣，姿势由拍摄类型决定
_MODEL_APPEARANCE_REF_PREFIX = (
    "[CRITICAL INSTRUCTION - MODEL APPEARANCE + LINGERIE SWAP]: "
    "The LAST reference image is a FULL MODEL REFERENCE. You MUST generate the EXACT SAME PERSON — "
    "same face, skin tone, body type, and hair as shown in this image. "
    "CRITICAL: Keep the model's pants/bottoms, shoes, and accessories EXACTLY THE SAME as in the reference image. "
    "The ONLY thing you must change is the LINGERIE TOP/BRA — replace it with the NEW product described below. "
    "Do NOT copy the pose from the reference image. Instead, follow the specific pose and angle instructions in the prompt below. "
    "The OTHER reference images show the NEW LINGERIE PRODUCT. STRICTLY replicate the exact structural design, color, pattern, "
    "and details of this new product. Do NOT change the new product design. "
    "TASK: Generate the same model from the last image, wearing the new lingerie from the other images, "
    "in the pose described below. Keep pants/bottoms, shoes, and accessories identical to the reference. "
)

# ============================================================
# 拍摄类型 (Shot Types)
# ============================================================
SHOT_TYPES = {
    # ---- 模特穿着类 ----
    "model_front": {
        "id": "model_front",
        "name": "模特正面图",
        "name_en": "Model Front View",
        "description": "模特穿上内衣的正面半身照，从颈部到大腿中部",
        "icon": "user",
        "category": "model",
        "needs_persona": True,
        "aspect_ratio": "3:4",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "[FIXED_MODEL_PERSONA] is wearing the EXACT lingerie described above — every detail "
            "including color, fabric texture, strap design, cup construction, closure system, and "
            "decorative elements must be perfectly preserved and identical to the description. "
            "Paired with matching color underwear bottoms. Standard front half-body shot from neck "
            "to mid-thigh, natural standing pose with hands relaxed at sides, face not fully visible, "
            "premium studio lighting with soft diffusion, clean neutral background, realistic skin "
            "texture, natural body proportions, high-end e-commerce photography. "
            "[TEXT_INSTRUCTION] --ar 3:4"
        ),
    },
    "model_back": {
        "id": "model_back",
        "name": "模特背面图",
        "name_en": "Model Back View",
        "description": "模特穿上内衣的纯背面视角，展示后背贴合度与面料过渡",
        "icon": "rotate-cw",
        "category": "model",
        "needs_persona": True,
        "aspect_ratio": "3:4",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "[FIXED_MODEL_PERSONA] is wearing the EXACT lingerie described above — every detail "
            "including color, fabric texture, strap design, cup construction, closure system, and "
            "decorative elements must be perfectly preserved and identical to the description. "
            "Paired with matching color underwear bottoms. Pure back straight view from nape of neck "
            "to lower back, arms resting naturally at sides, face not visible, minimalist studio "
            "background with soft rim light highlighting fabric texture and seamless skin transition, "
            "premium fine art photography, realistic skin texture. "
            "[TEXT_INSTRUCTION] --ar 3:4"
        ),
    },
    "model_side": {
        "id": "model_side",
        "name": "模特侧面图",
        "name_en": "Model Side View",
        "description": "3/4侧面视角，展示身体S型曲线和产品轮廓",
        "icon": "arrow-right",
        "category": "model",
        "needs_persona": True,
        "aspect_ratio": "3:4",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "[FIXED_MODEL_PERSONA] is wearing the EXACT lingerie described above — every detail "
            "including color, fabric texture, strap design, cup construction, closure system, and "
            "decorative elements must be perfectly preserved and identical to the description. "
            "Paired with matching color underwear bottoms. 3/4 side profile view from neck to hips, "
            "one hand resting gracefully to show the natural S-curve silhouette, face not visible, "
            "clean studio lighting emphasizing fabric contour and body line, neutral background, "
            "realistic skin texture. [TEXT_INSTRUCTION] --ar 3:4"
        ),
    },
    "model_three_view": {
        "id": "model_three_view",
        "name": "模特三视图",
        "name_en": "Model Three Views",
        "description": "正面+侧面+背面三视图合一，同一灯光同一模特",
        "icon": "columns",
        "category": "model",
        "needs_persona": True,
        "aspect_ratio": "16:9",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "Professional e-commerce three-view photography of [FIXED_MODEL_PERSONA] wearing the "
            "EXACT lingerie described above — every detail including color, fabric texture, strap "
            "design, cup construction, closure system, and decorative elements must be perfectly "
            "preserved and identical to the description. Left panel shows front view, center panel "
            "shows side view, right panel shows back view. Same lighting and pose height across all "
            "three views, white studio background, separated by thin vertical lines. Face not visible "
            "in any view. Realistic skin texture, natural body proportions, high-end catalog "
            "photography. [TEXT_INSTRUCTION] --ar 16:9"
        ),
    },

    "pose_reference": {
        "id": "pose_reference",
        "name": "跟随参考姿势",
        "name_en": "Reference Pose",
        "description": "1:1还原参考模特的姿势和外貌，只替换内衣为3D图款式，保留裤子/下装不变",
        "icon": "user",
        "category": "model",
        "needs_persona": True,
        "aspect_ratio": "3:4",
        "prompt_template": (
            "[CRITICAL INSTRUCTION - FULL MODEL REFERENCE + LINGERIE SWAP]:\n"
            "Reference Image 1 (FIRST image): A FULL MODEL REFERENCE photo.\n"
            "You MUST replicate the EXACT SAME PERSON — same face, skin tone, body type, hair,\n"
            "AND the EXACT SAME POSE — same body position, arm placement, hand position, leg stance, body angle, and camera framing.\n"
            "CRITICAL: Keep EVERYTHING from this reference model EXACTLY THE SAME — face, hair, skin, body, pants/bottoms,\n"
            "shoes, accessories, background, lighting. The ONLY thing you must change is the LINGERIE TOP/BRA.\n"
            "Reference Images 2+ (REMAINING images): The NEW LINGERIE PRODUCT to be worn INSTEAD of the original.\n"
            "STRICTLY replicate the exact structural design, color, pattern, straps, closure, lace details,\n"
            "and every detail of this NEW product. Do NOT change the new product design.\n"
            "TASK: Generate the EXACT SAME model in the EXACT SAME pose, wearing the NEW LINGERIE from images 2+\n"
            "instead of the original. Everything else must remain IDENTICAL to image 1.\n"
            "[POSE TO REPLICATE: {extracted_pose_description}]\n\n"
            "[IMAGE REFERENCE REQUIREMENT: Strictly replicate the exact structural design, color, pattern,\n"
            "and every detail of the provided reference image of the product].\n\n"
            "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n"
            "POSE DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_POSE_DNA]\n\n"
            "[FIXED_MODEL_PERSONA] is wearing the NEW lingerie described above INSTEAD of the original. "
            "The model is performing the EXACT SAME POSE as described in the POSE DESCRIPTION. "
            "Keep the model's pants/bottoms, shoes, and accessories IDENTICAL to the reference image. "
            "Every detail of the NEW lingerie including color, fabric texture, strap design, cup construction, closure system, and "
            "decorative elements must be perfectly preserved and identical to the product description. "
            "Premium studio lighting, clean neutral background, realistic skin texture, high-end e-commerce photography. "
            "[TEXT_INSTRUCTION] --ar 3:4"
        ),
    },
    # ---- 细节/材质类 ----
    "detail_closeup": {
        "id": "detail_closeup",
        "name": "细节特写",
        "name_en": "Detail Close-up",
        "description": "四格微距拼图：面料纹理、五金件、弹力演示、内部结构",
        "icon": "search",
        "category": "detail",
        "needs_persona": False,
        "aspect_ratio": "3:4",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "Four-grid macro photography layout of the EXACT lingerie described above — every "
            "detail must be perfectly preserved and identical to the description. "
            "Grid 1 extreme close-up of fabric texture and pattern, "
            "Grid 2 strap and closure hardware detail, "
            "Grid 3 elastic stretch demonstration with hands pulling fabric, "
            "Grid 4 interior construction and tagless label. "
            "8K resolution, studio macro lighting, sharp focus. [TEXT_INSTRUCTION] --ar 3:4"
        ),
    },
    "material_texture": {
        "id": "material_texture",
        "name": "面料展示",
        "name_en": "Material & Texture",
        "description": "极致微距，手部拉伸面料展示高弹力，背光透射效果",
        "icon": "layers",
        "category": "detail",
        "needs_persona": False,
        "aspect_ratio": "3:4",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "Extreme macro photography of the EXACT lingerie described above — every detail "
            "must be perfectly preserved and identical to the description. Hands stretching the "
            "fabric to demonstrate high elasticity, backlight transparency showing breathable mesh "
            "detail, focus on material texture and weave pattern, 8K resolution, tactile sensory "
            "photography. [TEXT_INSTRUCTION] --ar 3:4"
        ),
    },

    # ---- 场景类 ----
    "lifestyle_scene": {
        "id": "lifestyle_scene",
        "name": "场景穿搭",
        "name_en": "Lifestyle Scene",
        "description": "模特穿白T外搭，展示无勒痕隐形穿着效果，自然家居光",
        "icon": "home",
        "category": "scene",
        "needs_persona": True,
        "aspect_ratio": "3:4",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "Lifestyle photography, [FIXED_MODEL_PERSONA] wearing a fitted white t-shirt over "
            "the EXACT lingerie described above — every detail including color, fabric texture, "
            "strap design, cup construction, closure system, and decorative elements must be "
            "perfectly preserved and identical to the description. Smooth silhouette with no visible "
            "bra lines, natural morning light, modern minimalist home interior, authentic daily "
            "lifestyle moment, natural and relaxed pose, face not fully visible. "
            "[TEXT_INSTRUCTION] --ar 3:4"
        ),
    },

    # ---- 3D渲染类 ----
    "3d_product": {
        "id": "3d_product",
        "name": "3D产品渲染",
        "name_en": "3D Product Rendering",
        "description": "产品3D正/侧/背三视图，纯色背景，不使用人台，精准还原蕾丝等细节",
        "icon": "box",
        "category": "3d",
        "needs_persona": False,
        "aspect_ratio": "16:9",
        "prompt_template": (
            _REF_PREFIX
            + "PRODUCT DESCRIPTION (MUST BE REPRODUCED EXACTLY): [FIXED_PRODUCT_DNA]\n\n"
            + "Generate photorealistic 3D product renderings of the EXACT lingerie described above — "
            "every detail including color, fabric texture, strap design, cup construction, closure "
            "system, and decorative elements must be perfectly preserved and identical to the "
            "description. Three-panel layout — left panel front view, center panel 3/4 angle view, "
            "right panel back view. CRITICAL: faithfully reproduce the EXACT closure system "
            "(front hooks, back hooks, zipper), cup seam lines, strap attachment points, band "
            "construction, fabric texture and pattern, edge finishing (scalloped lace, bonded, "
            "raw-cut), and all hardware/decorative elements from the reference image. Pure solid "
            "color background (#F5F5F5). Product only — NO mannequin, NO human body, NO ghost "
            "mannequin effect. Product should appear as if floating with natural dimensional form "
            "showing the 3D shape. Cinematic studio lighting with soft shadows to reveal fabric "
            "depth and stitching detail. 8K resolution, photorealistic rendering quality. "
            "[TEXT_INSTRUCTION] Aspect ratio 16:9"
        ),
    },
}

# 向后兼容 — 保留旧变量名以免导入错误
MARKETS = {}
EXTRAS = {}
