"""LLM factory for the smart_agent project."""
from __future__ import annotations

from typing import Optional

from langchain_openai import ChatOpenAI

from config.model_utils import ModelConfig, get_default_model
from config.openai_compatible import ChatOpenAICompatible


def _build_chat_params(cfg: ModelConfig) -> dict:
    if cfg.max_tokens is not None and cfg.max_completion_tokens is not None:
        raise ValueError("max_tokens and max_completion_tokens are mutually exclusive")

    params = {
        "api_key": cfg.api_key,
        "base_url": cfg.base_url,
        "model": cfg.id,
        "temperature": cfg.temperature,
        "streaming": cfg.stream,
    }
    if cfg.top_p is not None:
        params["top_p"] = cfg.top_p
    if cfg.max_tokens is not None:
        params["max_tokens"] = cfg.max_tokens
    if cfg.max_completion_tokens is not None:
        params["max_completion_tokens"] = cfg.max_completion_tokens
    if cfg.frequency_penalty is not None:
        params["frequency_penalty"] = cfg.frequency_penalty
    if cfg.presence_penalty is not None:
        params["presence_penalty"] = cfg.presence_penalty
    if cfg.response_format is not None:
        params["response_format"] = cfg.response_format
    if cfg.stop is not None:
        params["stop"] = cfg.stop

    if cfg.provider_params:
        params.update(cfg.provider_params)
    return params


def get_llm(model: Optional[ModelConfig] = None, provider: Optional[str] = None):
    """Create and return a chat LLM instance from ModelConfig."""
    cfg = model or get_default_model(provider)
    if not cfg.api_key:
        raise ValueError(f"Missing API key for provider: {cfg.provider}")
    llm_class = ChatOpenAICompatible if cfg.provider == "huoshan" else ChatOpenAI
    return llm_class(**_build_chat_params(cfg))
