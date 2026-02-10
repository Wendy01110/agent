"""Executor prompt definitions."""
from __future__ import annotations


class ExecutorPrompt:
    system: str = (
        "你是执行智能体，只负责调用工具完成计划中的步骤。"
        "职责边界：\n"
        "1) 只执行计划，不改写计划目标；\n"
        "2) 必须通过工具获取结果，不自行编造；\n"
        "3) 仅使用提供的工具，严格按工具参数调用；\n"
        "4) 计算用 calculator，代码用 python，检索用 web_search\n"
        "5) 失败时给出原因并尝试替代工具或参数。\n"
        "输出要求：简洁，包含可直接使用的工具结果。"
    )
    human: str = "当前时间：{now}\n\n计划：\n{plan}\n\n用户请求：{input}"

    @classmethod
    def build(cls) -> tuple[str, str]:
        return cls.system, cls.human
