"""Callback handlers for streaming and tool logs."""
from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

from config.model_utils import ModelConfig, estimate_usage_cost, normalize_usage


class StreamCallbackHandler(BaseCallbackHandler):
    def __init__(self, label: str, include_tools: bool = False) -> None:
        self.label = label
        self.include_tools = include_tools
        self._started = False
        self._in_think = False

    def _ensure_label(self) -> None:
        if not self._started:
            print(f"\n[{self.label}]\n", flush=True)
            self._started = True

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self._ensure_label()
        chunk = kwargs.get("chunk")
        message = getattr(chunk, "message", None) if chunk is not None else None
        reasoning = None
        if message is not None:
            reasoning = getattr(message, "additional_kwargs", {}).get("reasoning_content")

        if reasoning:
            if not self._in_think:
                print("<think>", end="", flush=True)
                self._in_think = True
            print(reasoning, end="", flush=True)
            return
        if self._in_think:
            print("</think>", end="", flush=True)
            self._in_think = False
        print(token, end="", flush=True)

    def on_llm_end(self, response, **kwargs: Any) -> None:
        if self._in_think:
            print("</think>", end="", flush=True)
            self._in_think = False

    def on_tool_start(self, serialized: dict, input_str: str, **kwargs: Any) -> None:
        if not self.include_tools:
            return
        name = serialized.get("name") or serialized.get("id") or "tool"
        print(f"\n[TOOL START] {name} | input={input_str}\n", flush=True)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        if not self.include_tools:
            return
        print(f"\n[TOOL END] output={output}\n", flush=True)


class TokenUsageCallbackHandler(BaseCallbackHandler):
    def __init__(self, label: str, model: ModelConfig) -> None:
        self.label = label
        self.model = model

    def on_llm_end(self, response, **kwargs: Any) -> None:
        usage = None
        if getattr(response, "llm_output", None):
            for key in ("token_usage", "usage", "usage_metadata"):
                if key in response.llm_output:
                    usage = response.llm_output[key]
                    break
        if usage is None and response.generations:
            first_batch = response.generations[0]
            if first_batch:
                message = getattr(first_batch[0], "message", None)
                if message is not None:
                    usage = getattr(message, "usage_metadata", None)
        if not usage:
            return

        normalized = normalize_usage(usage)
        if not normalized:
            return

        cost = estimate_usage_cost(usage, self.model)
        if cost:
            print(
                f"\n[{self.label} USAGE] input={cost['input_tokens']} output={cost['output_tokens']} "
                f"total={cost['total_tokens']} cost≈{cost['total_cost']:.6f}元\n",
                flush=True,
            )
        else:
            print(
                f"\n[{self.label} USAGE] input={normalized['input_tokens']} output={normalized['output_tokens']} "
                f"total={normalized['total_tokens']}\n",
                flush=True,
            )
