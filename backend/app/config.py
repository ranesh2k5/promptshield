"""
Application configuration – loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    openai_api_key: str = ""
    secret_key: str = "changeme"
    allowed_origins: list[str] = ["http://localhost:5173"]
    use_mock_llm: bool = False


settings = Settings()
