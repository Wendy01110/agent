"""Model presets."""
from __future__ import annotations

from config.model_utils import ModelConfig, TokenPriceInfo
from config.env import get_env


HUOSHAN_DOUBAO = ModelConfig(
    provider="huoshan",
    id="doubao-seed-1-8-251228",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=get_env("HUOSHAN_API_KEY"),
    temperature=0.3,
    max_completion_tokens=4096,
    provider_params={
        "stream_options": {"include_usage": True},
        "extra_body": {
            "thinking": {"type": "enabled"},
            "reasoning_effort": "medium",
        },
    },
    token_price=(
        TokenPriceInfo((0, 32000), (0, 200), 0.8, 2),
        TokenPriceInfo((0, 32000), (200, None), 0.8, 8),
        TokenPriceInfo((32000, 128000), (0, None), 1.2, 16),
        TokenPriceInfo((128000, None), (0, None), 2.4, 24),
    ),
)


HUOSHAN_DEEPSEEK = ModelConfig(
    provider="huoshan",
    id="deepseek-v3-2-251201",
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=get_env("HUOSHAN_API_KEY"),
    temperature=0.2,
    max_completion_tokens=4096,
    provider_params={
        "stream_options": {"include_usage": True},
        "extra_body": {
            "thinking": {"type": "enabled"},
        },
    },
)
