"""LLM configuration for OpenRouter integration."""

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()


def get_llm(
    *,
    temperature: float = 0.7,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ChatOpenAI:
    """
    Get a configured ChatOpenAI instance for OpenRouter.

    Args:
        temperature: LLM temperature (default: 0.7)
        model: Override the model from environment
        api_key: Override the API key from environment
        base_url: Override the base URL from environment

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set
    """
    # Get configuration from environment or parameters
    llm_api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    llm_base_url = base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    llm_model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    if not llm_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Please set it in your environment or .env file."
        )

    return ChatOpenAI(
        model=llm_model,
        api_key=llm_api_key,
        base_url=llm_base_url,
        temperature=temperature,
    )
