from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_secret: str
    verify_token: str
    secret_key: str
    debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Facebook
    page_access_token: str

    # Database
    database_url: str

    # OpenAI Compatible API
    openai_api_key: str
    openai_base_url: str = "https://openrouter.ai/api/v1"
    model_name: str = "qwen/qwen3-8b:free"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # Admin
    admin_username: str
    admin_password: str

    # Logging
    log_level: str = "INFO"

    # Cache
    cache_enabled: bool = False
    redis_url: Optional[str] = "redis://localhost:6379/0"

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # AI Settings
    ai_max_tokens: int = 100
    ai_temperature: float = 0.7
    ai_max_comment_length: int = 500
    ai_min_comment_length: int = 2

    # System Prompt (Arabic)
    system_prompt: str = (
        "أنت مساعد صفحة Remix على فيسبوك. "
        "ردودك باللغة العربية فقط. "
        "الرد قصير جداً، بحد أقصى 15 كلمة. "
        "لا تكرر نفس الردود. "
        "لا تستخدم أسلوب خدمة العملاء. "
        "لا تستخدم عبارات تسويقية أو تطلب الشراء. "
        "إذا كان التعليق دعاء، رد بدعاء مناسب. "
        "إذا كان التعليق مدحاً، اشكر المستخدم بإيجاز. "
        "إذا كان التعليق إيموجي فقط، رد بشكل طبيعي ومختصر. "
        "إذا كان التعليق حزيناً، تعاطف باحترام وإيجاز. "
        "لا تدخل في السياسة أو الجدالات. "
        "ردك يجب أن يكون إنسانياً وطبيعياً."
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
