"""Langfuse callback integration helpers."""
from __future__ import annotations

import os
from typing import Optional

from langchain_core.callbacks import BaseCallbackHandler


def _is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_langfuse_kwargs() -> dict:
    mapping = {
        "public_key": "LANGFUSE_PUBLIC_KEY",
        "secret_key": "LANGFUSE_SECRET_KEY",
        "host": "LANGFUSE_HOST",
    }
    kwargs = {}
    for key, env_name in mapping.items():
        env_value = os.getenv(env_name, "").strip()
        if env_value:
            kwargs[key] = env_value
    return kwargs


def _load_callback_class():
    try:
        from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler

        return LangfuseCallbackHandler
    except Exception:
        return None


def build_langfuse_callback() -> Optional[BaseCallbackHandler]:
    """Return a Langfuse callback handler when LANGFUSE_ENABLED is true."""
    enabled = _is_enabled(os.getenv("LANGFUSE_ENABLED", "0"))
    if not enabled:
        return None

    callback_cls = _load_callback_class()
    if callback_cls is None:
        print("提示：已开启 LANGFUSE_ENABLED，但未安装 langfuse 或导入失败。")
        return None

    kwargs = _read_langfuse_kwargs()
    try:
        return callback_cls(**kwargs)
    except TypeError:
        return callback_cls()
