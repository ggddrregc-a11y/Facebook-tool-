from functools import lru_cache
from typing import Optional, List
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
    facebook_page_id: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # ── Grok / xAI Multi-Key Support ──────────────────────────────────────────
    # Primary key (required)
    grok_api_key: str = ""

    # Extra keys — add GROK_API_KEY_2, GROK_API_KEY_3 … GROK_API_KEY_10 in env
    grok_api_key_2: str = ""
    grok_api_key_3: str = ""
    grok_api_key_4: str = ""
    grok_api_key_5: str = ""
    grok_api_key_6: str = ""
    grok_api_key_7: str = ""
    grok_api_key_8: str = ""
    grok_api_key_9: str = ""
    grok_api_key_10: str = ""

    grok_base_url: str = "https://api.x.ai/v1"
    grok_model: str = "grok-3-mini"

    # Legacy OpenAI-compatible fallback (kept for backward compat)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.x.ai/v1"
    model_name: str = "grok-3-mini"

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

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

    # Post Generation Settings
    post_max_tokens: int = 500
    post_temperature: float = 0.85
    post_auto_approve: bool = False   # إذا True ينشر مباشرة بدون مراجعة
    post_scheduler_interval_seconds: int = 60  # كل كم ثانية يتحقق السكيدولر

    # Image Generation (DALL-E compatible endpoint if available)
    image_generation_enabled: bool = False
    image_generation_api_key: str = ""
    image_generation_base_url: str = "https://api.openai.com/v1"
    image_generation_model: str = "dall-e-3"

    # System Prompt for comments — لارا's personality
    system_prompt: str = (
        "اسمك لارا، بنت مصرية عندها 24 سنة، شخصيتك طبيعية ومرحة وقريبة من الناس. "
        "بتشتغلي مشرفة على صفحة Remix على فيسبوك وبتردي على تعليقات الناس كصاحبتهم. "
        "**قواعد ثابتة:** "
        "- ردك بالعربية العامية المصرية فقط، بلا تفكير أو شرح. "
        "- اكتبي الرد مباشرة بلا مقدمات. "
        "- الرد قصير جداً: جملة واحدة بحد أقصى 10 كلمات. "
        "- كوني طبيعية ومختلفة في كل رد، زي ما البشر بيردوا. "
        "- لا تستخدمي أسلوب خدمة عملاء أو كلام رسمي أبداً. "
        "- لا تقولي 'أنا لارا' أو تعرفي بنفسك في الردود. "
        "**أسلوبك حسب التعليق:** "
        "- دعاء → ردي بدعاء مصري دافي قصير زي 'ربنا يكرمك يا قلبي 🤍' "
        "- مدح أو إعجاب → اشكري بأسلوب بنت مصرية طبيعي زي 'يسلم قلبك والله 😊' "
        "- إيموجي فقط → ردي بإيموجي أو جملة خفيفة "
        "- حزن أو مشكلة → تعاطفي بجملة دافية بسيطة "
        "- غضب أو انتقاد → ردي بهدوء وذكاء بدون دفاعية "
        "- سؤال → أجيبي بشكل مختصر وطبيعي "
        "- مزاح → العبي معاه وارديها بطريقة طريفة "
        "- لا تدخلي في السياسة أو الجدال أبداً."
    )

    # System Prompt for post generation — لارا's voice
    post_system_prompt: str = (
        "اسمك لارا، بنت مصرية عندها 24 سنة، بتكتبي منشورات صفحة Remix على فيسبوك. "
        "أسلوبك: عامية مصرية خفيفة، صادقة، وقريبة من الناس — مش إعلان، كلام بنت عادية بتشارك حاجة حلوة. "
        "**قواعد المنشور:** "
        "- اكتبي المنشور مباشرة بلا مقدمات أو شرح. "
        "- 3 إلى 5 جمل طبيعية، مش طويلة. "
        "- في النهاية حطي 3-5 هاشتاقات مناسبة. "
        "- استخدمي إيموجي بشكل طبيعي مش مبالغ فيه. "
        "- خلي فيه روح ودفا زي ما بنت بتكتب لصحباتها. "
        "- متكرريش نفس الجمل أو الأفكار في منشورات مختلفة."
    )

    @property
    def all_grok_keys(self) -> List[str]:
        """Return all configured Grok API keys as a list (no empty strings)."""
        keys = [
            self.grok_api_key,
            self.grok_api_key_2,
            self.grok_api_key_3,
            self.grok_api_key_4,
            self.grok_api_key_5,
            self.grok_api_key_6,
            self.grok_api_key_7,
            self.grok_api_key_8,
            self.grok_api_key_9,
            self.grok_api_key_10,
        ]
        # Fall back to legacy openai_api_key
        if not any(k.strip() for k in keys) and self.openai_api_key:
            return [self.openai_api_key]
        return [k for k in keys if k and k.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
