"""Workflow orchestration for multi-agent collaboration."""
from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from config.llm import get_llm
from config.model_utils import get_default_model
from tools.registry import get_tools, describe_tools
from agents.planner import PlannerAgent
from agents.executor import ToolExecutorAgent
from agents.analyst import AnalystAgent
from workflow.callbacks import StreamCallbackHandler, TokenUsageCallbackHandler
from workflow.langfuse_callback import build_langfuse_callback


def run_flow(user_input: str, stream: bool = True) -> Dict[str, Any]:
    """Run planner -> executor -> analyst and return outputs."""
    model_cfg = get_default_model()
    llm = get_llm(model=model_cfg)
    tools = get_tools(llm)

    planner = PlannerAgent(llm)
    executor = ToolExecutorAgent(llm, tools)
    analyst = AnalystAgent(llm)
    tool_desc = describe_tools(tools)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    langfuse_cb = build_langfuse_callback()

    planner_cb = []
    executor_cb = []
    analyst_cb = []

    if stream:
        planner_cb.extend(
            [StreamCallbackHandler("PLANNER", include_tools=False), TokenUsageCallbackHandler("PLANNER", model_cfg)]
        )
        executor_cb.extend(
            [StreamCallbackHandler("EXECUTOR", include_tools=True), TokenUsageCallbackHandler("EXECUTOR", model_cfg)]
        )
        analyst_cb.extend(
            [StreamCallbackHandler("ANALYST", include_tools=False), TokenUsageCallbackHandler("ANALYST", model_cfg)]
        )

    if langfuse_cb is not None:
        planner_cb.append(langfuse_cb)
        executor_cb.append(langfuse_cb)
        analyst_cb.append(langfuse_cb)

    plan = planner.plan(
        user_input,
        tool_desc=tool_desc,
        now=now,
        callbacks=planner_cb or None,
    )
    exec_result = executor.execute(
        user_input=user_input,
        plan=plan,
        now=now,
        callbacks=executor_cb or None,
    )
    final_answer = analyst.summarize(
        user_input,
        plan,
        exec_result,
        tool_desc=tool_desc,
        now=now,
        callbacks=analyst_cb or None,
    )

    return {
        "plan": plan,
        "executor_result": exec_result,
        "final": final_answer,
    }
