from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/providers", tags=["providers"])

PROVIDER_PRESETS = [
    {
        "id": "gemini_official",
        "name": "Gemini 官方 (Google)",
        "base_url": "https://generativelanguage.googleapis.com",
        "api_protocol": "Google API",
        "default_model": "gemini-2.0-flash-exp",
        "description": "Google Gemini 官方直连，需开通 Gemini API",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_protocol": "OpenAI",
        "default_model": "google/gemini-2.0-flash-exp:free",
        "description": "OpenRouter 多模型聚合平台，支持免费模型",
    },
    {
        "id": "wuyun",
        "name": "乌云科技 (Wuyun)",
        "base_url": "https://api.wuyunkeji.com/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-3.1-flash-image-preview",
        "description": "乌云科技 Gemini 中转站，国内友好",
    },
    {
        "id": "openai_official",
        "name": "OpenAI 官方",
        "base_url": "https://api.openai.com/v1",
        "api_protocol": "OpenAI",
        "default_model": "dall-e-3",
        "description": "OpenAI 官方图像生成",
    },
    {
        "id": "ai_proxy",
        "name": "AiProxy",
        "base_url": "https://api.aiproxy.io/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "AiProxy 中转站，国内友好",
    },
    {
        "id": "ohmygpt",
        "name": "OhMyGPT",
        "base_url": "https://api.ohmygpt.com/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "OhMyGPT 中转站，国内友好",
    },
    {
        "id": "closeai",
        "name": "CloseAI",
        "base_url": "https://api.closeai-proxy.xyz/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "CloseAI 中转站",
    },
    {
        "id": "api2d",
        "name": "API2D",
        "base_url": "https://openai.api2d.net/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "API2D 中转站，老牌稳定",
    },
    {
        "id": "gptgod",
        "name": "GPTGod",
        "base_url": "https://api.gptgod.online/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "GPTGod 中转站",
    },
    {
        "id": "one_api",
        "name": "One API 中转",
        "base_url": "https://api.openai.com/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "One API 自建中转（需修改 Base URL）",
    },
    {
        "id": "new_api",
        "name": "New API 中转",
        "base_url": "https://api.openai.com/v1",
        "api_protocol": "OpenAI",
        "default_model": "gemini-2.0-flash",
        "description": "New API 自建中转（需修改 Base URL）",
    },
    {
        "id": "custom",
        "name": "自定义 (Custom)",
        "base_url": "",
        "api_protocol": "OpenAI",
        "default_model": "",
        "description": "自定义 API 端点，填写完整的 Base URL 和模型名",
    },
]


@router.get("/presets")
async def get_provider_presets():
    return PROVIDER_PRESETS
