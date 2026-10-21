
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from __PACKAGE_NAME__.core.config import Settings, get_settings


def create_chat_model(
    settings: Settings | None = None,
) -> BaseChatModel:
    """Create the configured LangChain chat model."""

    settings = settings or get_settings()

    common = {
        "model": settings.llm_model,
        "timeout": settings.llm_timeout_seconds,
    }

    if settings.llm_provider == "ollama":
        return ChatOllama(
            **common,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_max_tokens,
        )

    if settings.llm_provider == "openai":
        assert settings.openai_api_key is not None

        return ChatOpenAI(
            **common,
            api_key=settings.openai_api_key.get_secret_value(),
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            max_retries=2,
        )

    if settings.llm_provider == "anthropic":
        assert settings.anthropic_api_key is not None

        return ChatAnthropic(
            **common,
            api_key=settings.anthropic_api_key.get_secret_value(),
            max_tokens=settings.llm_max_tokens,
            max_retries=2,
        )

    # Settings validation should reject unsupported providers first.
    raise ValueError(
        f"Unsupported LLM provider: {settings.llm_provider}"
    )
