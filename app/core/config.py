from decimal import Decimal
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "电商运营自动化 Agent"
    app_version: str = "1.0.0"
    debug: bool = True
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'ecommerce.db'}"
    ai_api_key: str = ""
    ai_base_url: str = ""
    ai_model: str = ""
    ai_timeout_seconds: float = Field(default=60, gt=0, le=120)
    ai_pricing_model: str = ""
    ai_input_price_per_million_tokens: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )
    ai_output_price_per_million_tokens: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
