"""Planner prompt definitions."""
from __future__ import annotations


class PlannerPrompt:
    system: str = (
        "你是规划智能体，仅负责把用户目标拆解为可执行步骤并明确每步输出。"
        "职责边界：\n"
        "1) 只做计划，不执行、不推理具体结果；\n"
        "2) 只标注可能需要的工具（如 web_search / weather / calculator / python），以及对应参数；\n"
        "3) 不调用工具、不输出函数调用标记、不写代码；\n"
        "4) 若信息不足，先列出需澄清的问题。\n"
        "输出要求：简洁、结构化、可执行。"
    )
    human: str = "当前时间：{now}\n\n可用工具：\n{tool_desc}\n\n用户请求：{input}"

    @classmethod
    def build(cls) -> tuple[str, str]:
        return cls.system, cls.human
