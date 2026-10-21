
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderName = Literal["ollama", "openai", "anthropic"]


class Settings(BaseSettings):
    """Validated configuration for the application."""

    app_name: str = "AgentForge App"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    llm_provider: ProviderName = "ollama"
    llm_model: str = "llama3.2"
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=512, ge=1, le=32768)
    llm_timeout_seconds: float = Field(default=30.0, gt=0, le=600)

    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    ollama_base_url: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_provider_settings(self) -> "Settings":
        if not self.llm_model.strip():
            raise ValueError("LLM_MODEL must not be empty.")

        if self.llm_provider == "openai":
            if (
                self.openai_api_key is None
                or not self.openai_api_key.get_secret_value().strip()
            ):
                raise ValueError(
                    "A non-empty OPENAI_API_KEY is required."
                )

        if self.llm_provider == "anthropic":
            if (
                self.anthropic_api_key is None
                or not self.anthropic_api_key.get_secret_value().strip()
            ):
                raise ValueError(
                    "A non-empty ANTHROPIC_API_KEY is required."
                )

        if self.llm_provider == "ollama":
            if not self.ollama_base_url.strip():
                raise ValueError("OLLAMA_BASE_URL must not be empty.")

        return self


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings for the application."""
    return Settings()
