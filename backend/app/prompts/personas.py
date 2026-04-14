"""
模特设定指令词库
来源：完整提示词汇总.md - 第1章
"""

PERSONAS = {
    "european_natural": {
        "id": "european_natural",
        "name": "欧洲自然风模特",
        "name_en": "European Natural (UK Size 12)",
        "description": "UK 12/EU 40，自然雀斑，随意低发髻，自信放松，适用西欧成熟市场",
        "prompt": (
            "A natural, authentic European woman (UK Size 12 / EU 40, realistic and healthy curves), "
            "subtle natural freckles, confident and relaxed gaze, natural dirty blonde or brunette hair "
            "styled in a messy low bun."
        ),
        "suitable_markets": ["germany", "western_europe"]
    },
    "influencer": {
        "id": "influencer",
        "name": "网红风模特",
        "name_en": "Influencer Style (UK Size 8)",
        "description": "UK 8/EU 36，紧致沙漏身材，金色美黑肤色，金链首饰法式美甲，适用快时尚市场",
        "prompt": (
            "A trendy, sun-kissed fashion model (UK Size 8 / EU 36, fit hourglass figure with a toned waist), "
            "smooth golden-tan skin, confident and chic vibe, wearing gold chunky chain jewelry, manicured hands "
            "with french tips, soft daylight studio lighting."
        ),
        "suitable_markets": ["western_europe", "functional"]
    },
    "headless": {
        "id": "headless",
        "name": "无头/半身展示",
        "name_en": "Headless Torso",
        "description": "不露脸躯干特写，阳光小麦色肤色，聚焦产品上身效果",
        "prompt": (
            "Cropped close-up shot of a female torso, sun-kissed skin, collarbone highlighted, "
            "wearing gold necklace, head out of frame, white sweatpants bottom."
        ),
        "suitable_markets": ["germany", "western_europe", "latin_america", "functional"]
    },
    "latin_america": {
        "id": "latin_america",
        "name": "拉美模特 (哥伦比亚)",
        "name_en": "Latin America (Colombian)",
        "description": "无头躯干+大腿上部，梨形沙漏复合身材，温暖定向光，真实皮肤质感",
        "prompt": (
            "A close-up framing of the torso and upper thighs, headless. Focuses on natural body curves "
            "and realistic skin pores under warm, directional light. The body shape is a standard Colombian "
            '"Pear-Hourglass" hybrid. The composition is centered and stable, emphasizing structural balance.'
        ),
        "suitable_markets": ["latin_america"]
    },
}
