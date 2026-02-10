"""Environment loading utilities."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

def _find_env_path() -> Optional[Path]:
    candidate = Path.cwd() / ".env"
    return candidate if candidate.is_file() else None


def load_env_file() -> None:
    """Load .env into os.environ (no-op if not found)."""
    env_path = _find_env_path()
    if not env_path:
        print("提示：未找到 .env 文件（当前工作目录）。")
        return
    load_dotenv(env_path)


def get_env(key: str, default: str = "") -> str:
    """Load .env (if present) and read env var."""
    load_env_file()
    return os.getenv(key, default)
