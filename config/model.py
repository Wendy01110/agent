"""Model presets."""
from __future__ import annotations

from config.env import get_env
from config.model_utils import ModelConfig, TokenPriceInfo

DEFAULT_ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
ARK_API_KEY = get_env("ARK_API_KEY") or get_env("HUOSHAN_API_KEY")
ARK_BASE_URL = get_env("ARK_BASE_URL", DEFAULT_ARK_BASE_URL)


DOUBAO_SEED_1_8 = ModelConfig(
    provider="huoshan",
    id="doubao-seed-1-8-251228",
    base_url=ARK_BASE_URL,
    api_key=ARK_API_KEY,
    temperature=0.3,
    max_completion_tokens=5000,
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

DOUBAO_SEED_2_0_PRO = ModelConfig(
    provider="huoshan",
    id="doubao-seed-2-0-pro-260215",
    base_url=ARK_BASE_URL,
    api_key=ARK_API_KEY,
    temperature=0.3,
    max_completion_tokens=5000,
    provider_params={
        "stream_options": {"include_usage": True},
        "extra_body": {
            "thinking": {"type": "enabled"},
            "reasoning_effort": "medium",
        },
    },
    token_price=(
        TokenPriceInfo((0, 32000), (0, None), 3.2, 16),
        TokenPriceInfo((32000, 128000), (0, None), 4.8, 24),
        TokenPriceInfo((128000, None), (0, None), 9.6, 48),
    ),
)

DOUBAO_SEED_2_0_LITE = ModelConfig(
    provider="huoshan",
    id="doubao-seed-2-0-lite-260215",
    base_url=ARK_BASE_URL,
    api_key=ARK_API_KEY,
    temperature=0.3,
    max_completion_tokens=5000,
    provider_params={
        "stream_options": {"include_usage": True},
        "extra_body": {
            "thinking": {"type": "enabled"},
            "reasoning_effort": "medium",
        },
    },
    token_price=(
        TokenPriceInfo((0, 32000), (0, None), 0.6, 1.2),
        TokenPriceInfo((32000, 128000), (0, None), 0.9, 5.4),
        TokenPriceInfo((128000, None), (0, None), 1.8, 10.8),
    ),
)

HUOSHAN_DEEPSEEK = ModelConfig(
    provider="huoshan",
    id="deepseek-v3-2-251201",
    base_url=ARK_BASE_URL,
    api_key=ARK_API_KEY,
    temperature=0.2,
    max_completion_tokens=5000,
    provider_params={
        "stream_options": {"include_usage": True},
        "extra_body": {
            "thinking": {"type": "enabled"},
        },
    },
)

MODEL_CHOICES = [
    {"label": "Doubao-Seed-1.8", "id": DOUBAO_SEED_1_8.id, "config": DOUBAO_SEED_1_8},
    {"label": "Doubao-Seed-2.0-pro", "id": DOUBAO_SEED_2_0_PRO.id, "config": DOUBAO_SEED_2_0_PRO},
    {"label": "Doubao-Seed-2.0-lite", "id": DOUBAO_SEED_2_0_LITE.id, "config": DOUBAO_SEED_2_0_LITE},
]

DEFAULT_MODEL_ID = DOUBAO_SEED_2_0_LITE.id
