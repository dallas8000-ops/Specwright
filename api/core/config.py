from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SPECWRIGHT_",
        extra="ignore",
    )

    app_name: str = "Specwright"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///specwright.db"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]
    workspace_root: Path = Path(__file__).resolve().parents[2]
    max_scan_files: int = 500
    frontend_url: str = "http://localhost:5173"

    watch_interval_seconds: int = 3

    slack_webhook_url: str = ""
    notion_api_key: str = ""
    notion_parent_page_id: str = ""

    github_token: str = ""
    github_webhook_secret: str = ""

    ai_api_key: str = ""
    ai_api_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_auto_on_scan: bool = True

    # Pricing (public catalog defaults)
    starter_price_usd: int = 29
    pro_price_usd: int = 79
    pro_trial_days: int = 14
    annual_discount_percent: int = 20

    # Stripe — mock only for local dev; never surfaced in UI
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_starter: str = ""
    stripe_price_id_pro: str = ""
    billing_mock_mode: bool = False


settings = Settings()
