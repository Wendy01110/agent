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
    planner_cb = (
        [StreamCallbackHandler("PLANNER", include_tools=False), TokenUsageCallbackHandler("PLANNER", model_cfg)]
        if stream
        else None
    )
    executor_cb = (
        [StreamCallbackHandler("EXECUTOR", include_tools=True), TokenUsageCallbackHandler("EXECUTOR", model_cfg)]
        if stream
        else None
    )
    analyst_cb = (
        [StreamCallbackHandler("ANALYST", include_tools=False), TokenUsageCallbackHandler("ANALYST", model_cfg)]
        if stream
        else None
    )

    plan = planner.plan(user_input, tool_desc=tool_desc, now=now, callbacks=planner_cb)
    exec_result = executor.execute(
        user_input=user_input, plan=plan, now=now, callbacks=executor_cb
    )
    final_answer = analyst.summarize(
        user_input, plan, exec_result, tool_desc=tool_desc, now=now, callbacks=analyst_cb
    )

    return {
        "plan": plan,
        "executor_result": exec_result,
        "final": final_answer,
    }
