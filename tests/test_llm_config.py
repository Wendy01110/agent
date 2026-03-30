import os
import pytest

from config.llm import get_llm, _build_chat_params
from config.model import HUOSHAN_DEEPSEEK, DEFAULT_MODEL_ID
from config.model_utils import (
    ModelConfig,
    estimate_usage_cost,
    normalize_usage,
    get_default_model,
    get_model_by_id,
    list_models,
)


def test_get_llm_uses_model_config():
    cfg = ModelConfig(
        provider="huoshan",
        id="ep-test",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="test-key",
        temperature=0.2,
        provider_params={"reasoning_effort": "medium"},
        max_completion_tokens=1024,
    )
    llm = get_llm(model=cfg)
    assert getattr(llm, "model_name", None) == "ep-test"
    assert getattr(llm, "streaming", False) is True


def test_build_chat_params_moves_stream_options_to_model_kwargs():
    cfg = ModelConfig(
        provider="huoshan",
        id="ep-test",
        base_url="https://example.com/v1",
        api_key="test-key",
        provider_params={
            "stream_options": {"include_usage": True},
            "extra_body": {"thinking": {"type": "enabled"}},
        },
    )
    params = _build_chat_params(cfg)
    assert "stream_options" not in params
    assert params["model_kwargs"]["stream_options"] == {"include_usage": True}
    assert params["extra_body"] == {"thinking": {"type": "enabled"}}


def test_model_registry_and_default():
    models = list_models("huoshan")
    model_ids = {item["id"] for item in models}
    assert {
        "doubao-seed-1-8-251228",
        "doubao-seed-2-0-pro-260215",
        "doubao-seed-2-0-lite-260215",
    }.issubset(model_ids)
    assert get_default_model().id == DEFAULT_MODEL_ID
    assert get_model_by_id(DEFAULT_MODEL_ID).id == DEFAULT_MODEL_ID


@pytest.mark.skipif(
    os.getenv("RUN_LLM_INTEGRATION") != "1",
    reason="Set RUN_LLM_INTEGRATION=1 to run live LLM call.",
)
def test_llm_integration_call():
    llm = get_llm()
    result = llm.invoke("ping")
    usage = getattr(result, "usage_metadata", None) or {}
    normalized = normalize_usage(usage)
    cost = estimate_usage_cost(usage, get_default_model())
    reasoning = getattr(result, "additional_kwargs", {}).get("reasoning_content")
    print("LLM response:", result)
    print("LLM usage:", normalized)
    if reasoning:
        print("LLM reasoning:", reasoning)
    if cost:
        print(
            "LLM cost: input={input_tokens} output={output_tokens} total={total_tokens} cost≈{total_cost:.6f}元".format(
                **cost
            )
        )
    assert result is not None


@pytest.mark.skipif(
    os.getenv("RUN_LLM_INTEGRATION") != "1",
    reason="Set RUN_LLM_INTEGRATION=1 to run live LLM call.",
)
def test_llm_stream_reasoning():
    llm = get_llm(HUOSHAN_DEEPSEEK)
    reasoning_chunks = []
    for chunk in llm.stream("ping"):
        message = getattr(chunk, "message", None)
        print("LLM chunk:", chunk)
        if message is None:
            continue
        reasoning = getattr(message, "additional_kwargs", {}).get("reasoning_content")
        if reasoning:
            reasoning_chunks.append(reasoning)
    print("LLM reasoning chunks:", reasoning_chunks)
    assert reasoning_chunks is not None
