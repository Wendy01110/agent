"""Workflow orchestration for multi-agent collaboration."""
from __future__ import annotations

from typing import Dict, Any, Sequence, Optional, Callable
from datetime import datetime
from uuid import uuid4

from config.llm import get_llm
from config.model_utils import get_default_model, get_model_by_id
from tools.registry import get_tools, describe_tools
from agents.planner import PlannerAgent
from agents.executor import ToolExecutorAgent
from agents.analyst import AnalystAgent
from workflow.callbacks import (
    StreamCallbackHandler,
    TokenUsageCallbackHandler,
    TraceCallbackHandler,
    StageStreamCallbackHandler,
)
from workflow.langfuse_callback import build_langfuse_callback
from workflow.run_logger import append_run_log


class BaseWorkflow:
    """Base workflow contract."""

    name: str = "base"

    def run(
        self,
        user_input: str,
        stream: bool = True,
        enabled_tool_names: Optional[Sequence[str]] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        raise NotImplementedError("workflow must implement run()")


class MultiAgentWorkflow(BaseWorkflow):
    """Planner -> Executor -> Analyst multi-agent workflow."""

    name = "multiagent"

    def _select_tools(self, tools: Sequence[Any], enabled_tool_names: Optional[Sequence[str]]) -> list[Any]:
        if not enabled_tool_names:
            return list(tools)
        selected = [tool for tool in tools if tool.name in set(enabled_tool_names)]
        return selected if selected else list(tools)

    @staticmethod
    def _safe_text(value: Any) -> str:
        if isinstance(value, str):
            return value
        return str(value)

    @staticmethod
    def _normalize_steps(intermediate_steps: Sequence[Any]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for step in intermediate_steps:
            if not isinstance(step, (list, tuple)) or len(step) != 2:
                normalized.append({"tool": "unknown", "input": "", "output": str(step)})
                continue
            action, observation = step
            normalized.append(
                {
                    "tool": getattr(action, "tool", "unknown"),
                    "input": MultiAgentWorkflow._safe_text(getattr(action, "tool_input", "")),
                    "output": MultiAgentWorkflow._safe_text(observation),
                }
            )
        return normalized

    def run(
        self,
        user_input: str,
        stream: bool = True,
        enabled_tool_names: Optional[Sequence[str]] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run planner -> executor -> analyst and return outputs."""
        model_cfg = get_model_by_id(model_id) if model_id else get_default_model()
        llm = get_llm(model=model_cfg)
        tools = self._select_tools(get_tools(llm), enabled_tool_names)

        planner = PlannerAgent(llm)
        executor = ToolExecutorAgent(llm, tools)
        analyst = AnalystAgent(llm)
        tool_desc = describe_tools(tools)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_id = str(uuid4())
        langfuse_cb = build_langfuse_callback()

        planner_cb = []
        executor_cb = []
        analyst_cb = []
        planner_trace = TraceCallbackHandler("PLANNER", include_tools=False)
        executor_trace = TraceCallbackHandler("EXECUTOR", include_tools=True)
        analyst_trace = TraceCallbackHandler("ANALYST", include_tools=False)
        planner_cb.append(planner_trace)
        executor_cb.append(executor_trace)
        analyst_cb.append(analyst_trace)

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
        normalized_steps = self._normalize_steps(exec_result.get("intermediate_steps", []))
        agent_traces = {
            "planner": {
                "input": {
                    "user_input": user_input,
                    "tool_desc": tool_desc,
                    "now": now,
                },
                "output": {"plan": plan},
                "reasoning": planner_trace.llm_calls[-1]["reasoning"] if planner_trace.llm_calls else "",
                "llm_calls": planner_trace.llm_calls,
            },
            "executor": {
                "input": {
                    "user_input": user_input,
                    "plan": plan,
                    "now": now,
                },
                "output": {"output": self._safe_text(exec_result.get("output", ""))},
                "reasoning": executor_trace.llm_calls[-1]["reasoning"] if executor_trace.llm_calls else "",
                "llm_calls": executor_trace.llm_calls,
                "tool_calls": normalized_steps,
                "callback_tool_calls": executor_trace.tool_calls,
            },
            "analyst": {
                "input": {
                    "user_input": user_input,
                    "plan": plan,
                    "tool_outputs": normalized_steps,
                    "tool_desc": tool_desc,
                    "now": now,
                },
                "output": {"final": final_answer},
                "reasoning": analyst_trace.llm_calls[-1]["reasoning"] if analyst_trace.llm_calls else "",
                "llm_calls": analyst_trace.llm_calls,
            },
        }

        result = {
            "run_id": run_id,
            "workflow": self.name,
            "model_id": model_cfg.id,
            "tools": [tool.name for tool in tools],
            "plan": plan,
            "executor_result": {
                "output": self._safe_text(exec_result.get("output", "")),
                "intermediate_steps": normalized_steps,
            },
            "agent_traces": agent_traces,
            "final": final_answer,
        }
        append_run_log(result)

        return result

    def run_streaming(
        self,
        user_input: str,
        enabled_tool_names: Optional[Sequence[str]] = None,
        event_sink: Optional[Callable[[dict[str, Any]], None]] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run workflow and emit incremental stage updates through event_sink."""
        sink = event_sink or (lambda event: None)
        model_cfg = get_model_by_id(model_id) if model_id else get_default_model()
        llm = get_llm(model=model_cfg)
        tools = self._select_tools(get_tools(llm), enabled_tool_names)

        planner = PlannerAgent(llm)
        executor = ToolExecutorAgent(llm, tools)
        analyst = AnalystAgent(llm)
        tool_desc = describe_tools(tools)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_id = str(uuid4())
        langfuse_cb = build_langfuse_callback()

        planner_trace = TraceCallbackHandler("PLANNER", include_tools=False)
        executor_trace = TraceCallbackHandler("EXECUTOR", include_tools=True)
        analyst_trace = TraceCallbackHandler("ANALYST", include_tools=False)
        planner_stream = StageStreamCallbackHandler("PLANNER", sink)
        executor_stream = StageStreamCallbackHandler("EXECUTOR", sink)
        analyst_stream = StageStreamCallbackHandler("ANALYST", sink)

        planner_cb = [planner_trace, planner_stream]
        executor_cb = [executor_trace, executor_stream]
        analyst_cb = [analyst_trace, analyst_stream]
        if langfuse_cb is not None:
            planner_cb.append(langfuse_cb)
            executor_cb.append(langfuse_cb)
            analyst_cb.append(langfuse_cb)

        sink(
            {
                "type": "meta",
                "run_id": run_id,
                "workflow": self.name,
                "model_id": model_cfg.id,
                "tools": [t.name for t in tools],
            }
        )

        plan = planner.plan(
            user_input,
            tool_desc=tool_desc,
            now=now,
            callbacks=planner_cb,
        )
        sink(
            {
                "type": "agent_done",
                "agent": "planner",
                "reasoning": planner_stream.reasoning_text,
                "answer": plan,
            }
        )

        exec_result = executor.execute(
            user_input=user_input,
            plan=plan,
            now=now,
            callbacks=executor_cb,
        )
        sink(
            {
                "type": "agent_done",
                "agent": "executor",
                "reasoning": executor_stream.reasoning_text,
                "answer": self._safe_text(exec_result.get("output", "")),
            }
        )

        final_answer = analyst.summarize(
            user_input,
            plan,
            exec_result,
            tool_desc=tool_desc,
            now=now,
            callbacks=analyst_cb,
        )
        sink(
            {
                "type": "agent_done",
                "agent": "analyst",
                "reasoning": analyst_stream.reasoning_text,
                "answer": final_answer,
            }
        )

        normalized_steps = self._normalize_steps(exec_result.get("intermediate_steps", []))
        agent_traces = {
            "planner": {
                "input": {"user_input": user_input, "tool_desc": tool_desc, "now": now},
                "output": {"plan": plan},
                "reasoning": planner_trace.llm_calls[-1]["reasoning"] if planner_trace.llm_calls else "",
                "llm_calls": planner_trace.llm_calls,
            },
            "executor": {
                "input": {"user_input": user_input, "plan": plan, "now": now},
                "output": {"output": self._safe_text(exec_result.get("output", ""))},
                "reasoning": executor_trace.llm_calls[-1]["reasoning"] if executor_trace.llm_calls else "",
                "llm_calls": executor_trace.llm_calls,
                "tool_calls": normalized_steps,
                "callback_tool_calls": executor_trace.tool_calls,
            },
            "analyst": {
                "input": {
                    "user_input": user_input,
                    "plan": plan,
                    "tool_outputs": normalized_steps,
                    "tool_desc": tool_desc,
                    "now": now,
                },
                "output": {"final": final_answer},
                "reasoning": analyst_trace.llm_calls[-1]["reasoning"] if analyst_trace.llm_calls else "",
                "llm_calls": analyst_trace.llm_calls,
            },
        }

        result = {
            "run_id": run_id,
            "workflow": self.name,
            "model_id": model_cfg.id,
            "tools": [tool.name for tool in tools],
            "plan": plan,
            "executor_result": {
                "output": self._safe_text(exec_result.get("output", "")),
                "intermediate_steps": normalized_steps,
            },
            "agent_traces": agent_traces,
            "final": final_answer,
        }
        append_run_log(result)
        sink(
            {
                "type": "done",
                "message": {"user": user_input, "assistant": final_answer},
                "result": result,
            }
        )
        return result


def run_flow(
    user_input: str,
    stream: bool = True,
    enabled_tool_names: Optional[Sequence[str]] = None,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Compatibility wrapper for legacy function-based entry."""
    return MultiAgentWorkflow().run(
        user_input=user_input,
        stream=stream,
        enabled_tool_names=enabled_tool_names,
        model_id=model_id,
    )
