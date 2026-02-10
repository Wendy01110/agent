"""Tool registry for smart_agent."""
from __future__ import annotations

from typing import List

from langchain_core.tools import Tool

from tools.web_search import WebSearchTool
from tools.weather import WeatherTool
from tools.bocha_search import BochaSearchTool
from tools.math_python_tools import CalculatorTool, PythonTool


def describe_tools(tools: List[Tool]) -> str:
    """Return a concise tool catalog for prompts."""
    lines = []
    for tool in tools:
        schema = getattr(tool, "args_schema", None)
        if schema:
            fields = schema.model_fields
            args_desc = ", ".join(
                f"{name}: {field.description or ''}".strip()
                for name, field in fields.items()
            )
        else:
            args_desc = ""
        lines.append(f"- {tool.name}: {tool.description}")
        if args_desc:
            lines.append(f"  参数: {args_desc}")
    return "\n".join(lines)


def get_tools(llm) -> List[Tool]:
    """Return the list of tools available to the ToolExecutorAgent."""
    return [
        CalculatorTool(llm),
        PythonTool(),
        WebSearchTool(),
        BochaSearchTool(),
        WeatherTool(),
    ]
