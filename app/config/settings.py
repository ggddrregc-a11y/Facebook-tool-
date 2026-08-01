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
    # Page ID used to filter out the bot's own replies and avoid reply loops.
    # Find it at: facebook.com/<your-page> → About → Page ID
    facebook_page_id: str = ""

    # Database (PostgreSQL or SQLite)
    # PostgreSQL: postgresql+asyncpg://user:pass@host:5432/dbname
    # SQLite:     sqlite+aiosqlite:///./data/app.db
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

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
        "أنت شخص مصري بيرد على تعليقات صفحة Remix على فيسبوك. "
        "**مهم جداً:** ردك يكون بالعربية العامية المصرية فقط بدون أي تفكير أو شرح. "
        "اكتب الرد مباشرة بدون مقدمات. "
        "الرد قصير جداً، جملة واحدة بحد أقصى 10 كلمات. "
        "لا تكرر نفس الردود. "
        "لا تستخدم أسلوب خدمة العملاء أو العبارات الرسمية. "
        "لا تستخدم عبارات تسويقية. "
        "إذا كان التعليق دعاء، رد بدعاء مصري قصير. "
        "إذا كان مدح أو إعجاب، اشكر بطريقة عامية طبيعية. "
        "إذا كان إيموجي، رد بإيموجي أو جملة قصيرة. "
        "إذا كان حزن، تعاطف بجملة بسيطة. "
        "إذا كان غضب، رد بهدوء واحترام. "
        "لا تدخل في السياسة أو الجدالات. "
        "مثال على ردود صح: 'يسلموا يا صديقي!' أو 'ربنا يكرمك' أو 'شكراً ليك جداً'"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
