import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_local_env() -> None:
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.isfile(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env()


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# 静态文件目录
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_IMAGES_DIR = os.path.join(STATIC_DIR, "generated")

# 应用基础配置
APP_BRAND_NAME = os.getenv("APP_BRAND_NAME", "奥拉·灵感")

# 数据库
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# 管理员账号
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 平台免费 API（可被数据库中的后台设置覆盖）
PLATFORM_API_DISPLAY_NAME = os.getenv("PLATFORM_API_DISPLAY_NAME", "云雾平台免费 API")
PLATFORM_API_BASE_URL = os.getenv("PLATFORM_API_BASE_URL", "https://api.wuyunkeji.com/v1")
PLATFORM_API_KEY = os.getenv("PLATFORM_API_KEY", "")
PLATFORM_API_MODEL_NAME = os.getenv("PLATFORM_API_MODEL_NAME", "gemini-3.1-flash-image-preview")
PLATFORM_API_PROTOCOL = os.getenv("PLATFORM_API_PROTOCOL", "OpenAI")
PLATFORM_FREE_GENERATIONS = int(os.getenv("PLATFORM_FREE_GENERATIONS", "3"))

# 邮箱验证码登录 - Brevo API 优先
BREVO_API_BASE_URL = os.getenv("BREVO_API_BASE_URL", "https://api.brevo.com/v3").rstrip("/")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "").strip()
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "").strip()
BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", APP_BRAND_NAME).strip() or APP_BRAND_NAME

# 邮箱验证码登录 - SMTP 备用
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", APP_BRAND_NAME).strip() or APP_BRAND_NAME
SMTP_USE_TLS = _env_flag("SMTP_USE_TLS", False)
SMTP_USE_SSL = _env_flag("SMTP_USE_SSL", True)
EMAIL_LOGIN_DEBUG = _env_flag("EMAIL_LOGIN_DEBUG", False)
EMAIL_LOGIN_CODE_TTL_MINUTES = int(os.getenv("EMAIL_LOGIN_CODE_TTL_MINUTES", "10"))
EMAIL_LOGIN_RESEND_COOLDOWN_SECONDS = int(os.getenv("EMAIL_LOGIN_RESEND_COOLDOWN_SECONDS", "60"))
EMAIL_LOGIN_MAX_SENDS_PER_HOUR = int(os.getenv("EMAIL_LOGIN_MAX_SENDS_PER_HOUR", "6"))
EMAIL_LOGIN_MAX_VERIFY_ATTEMPTS = int(os.getenv("EMAIL_LOGIN_MAX_VERIFY_ATTEMPTS", "5"))
