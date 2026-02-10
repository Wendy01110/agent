"""Model configuration types and helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class TokenPriceInfo:
    input_token_condition: tuple[int, Optional[int]]
    output_token_condition: tuple[int, Optional[int]]
    input_price: float
    output_price: float


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    id: str
    base_url: str
    api_key: str
    temperature: float = 0.0
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stream: bool = True
    response_format: Optional[dict[str, Any]] = None
    stop: Optional[list[str] | str] = None
    token_price: tuple[TokenPriceInfo, ...] = ()
    provider_params: dict[str, Any] = field(default_factory=dict)


def _in_range(value: float, min_value: Optional[int], max_value: Optional[int]) -> bool:
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def select_price_tier(
    token_price: tuple[TokenPriceInfo, ...],
    input_tokens: int,
    output_tokens: int,
) -> Optional[TokenPriceInfo]:
    if not token_price:
        return None
    for tier in token_price:
        in_min, in_max = tier.input_token_condition
        out_min, out_max = tier.output_token_condition
        if _in_range(input_tokens, in_min, in_max) and _in_range(output_tokens, out_min, out_max):
            return tier
    return None


def normalize_usage(usage: dict[str, Any]) -> dict[str, int]:
    if "input_tokens" in usage:
        return {
            "input_tokens": int(usage.get("input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
    if "prompt_tokens" in usage:
        return {
            "input_tokens": int(usage.get("prompt_tokens", 0)),
            "output_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
    return {}


def estimate_usage_cost(usage: dict[str, Any], model: ModelConfig) -> Optional[dict[str, Any]]:
    normalized = normalize_usage(usage)
    if not normalized:
        return None
    tier = select_price_tier(
        model.token_price,
        normalized["input_tokens"],
        normalized["output_tokens"],
    )
    if tier is None:
        return None
    input_cost = normalized["input_tokens"] / 1_000_000 * tier.input_price
    output_cost = normalized["output_tokens"] / 1_000_000 * tier.output_price
    return {
        "input_tokens": normalized["input_tokens"],
        "output_tokens": normalized["output_tokens"],
        "total_tokens": normalized["total_tokens"],
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
        "tier": tier,
    }


def get_default_model(provider: str | None = None) -> ModelConfig:
    if provider in (None, "huoshan"):
        # Lazy import to avoid circular dependency with config.model
        from config.model import HUOSHAN_DOUBAO

        return HUOSHAN_DOUBAO
    raise ValueError(f"Unknown provider: {provider}")
