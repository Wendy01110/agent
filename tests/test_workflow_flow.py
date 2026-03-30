from types import SimpleNamespace

from workflow.flow import MultiAgentWorkflow, run_flow


def test_multiagent_workflow_supports_tool_filter(monkeypatch):
    monkeypatch.setattr(
        "workflow.flow.get_default_model",
        lambda provider=None: SimpleNamespace(id="dummy-model"),
    )
    monkeypatch.setattr("workflow.flow.get_llm", lambda model=None: object())
    monkeypatch.setattr(
        "workflow.flow.get_tools",
        lambda llm: [
            SimpleNamespace(name="calculator", description="calc"),
            SimpleNamespace(name="weather", description="weather"),
        ],
    )
    monkeypatch.setattr("workflow.flow.describe_tools", lambda tools: ",".join(t.name for t in tools))
    monkeypatch.setattr("workflow.flow.build_langfuse_callback", lambda: None)
    monkeypatch.setattr("workflow.flow.append_run_log", lambda payload: None)

    class DummyPlanner:
        def __init__(self, llm):
            pass

        def plan(self, user_input, tool_desc, now, callbacks=None):
            return f"plan({tool_desc})"

    class DummyExecutor:
        def __init__(self, llm, tools):
            self.tools = tools

        def execute(self, user_input, plan, now, callbacks=None):
            return {"intermediate_steps": [], "output": f"exec:{[t.name for t in self.tools]}"}

    class DummyAnalyst:
        def __init__(self, llm):
            pass

        def summarize(self, user_input, plan, result, tool_desc, now, callbacks=None):
            return f"final:{plan}:{tool_desc}:{result['output']}"

    monkeypatch.setattr("workflow.flow.PlannerAgent", DummyPlanner)
    monkeypatch.setattr("workflow.flow.ToolExecutorAgent", DummyExecutor)
    monkeypatch.setattr("workflow.flow.AnalystAgent", DummyAnalyst)

    result = MultiAgentWorkflow().run(
        user_input="测试",
        stream=False,
        enabled_tool_names=["weather"],
    )

    assert result["workflow"] == "multiagent"
    assert result["tools"] == ["weather"]
    assert result["plan"] == "plan(weather)"
    assert "exec:['weather']" in result["final"]


def test_run_flow_compatibility_wrapper(monkeypatch):
    captured = {}

    def fake_run(self, user_input, stream=True, enabled_tool_names=None, model_id=None):
        captured["user_input"] = user_input
        captured["stream"] = stream
        captured["enabled_tool_names"] = enabled_tool_names
        captured["model_id"] = model_id
        return {"ok": True}

    monkeypatch.setattr(MultiAgentWorkflow, "run", fake_run)
    result = run_flow("hello", stream=False, enabled_tool_names=["calculator"], model_id="m1")

    assert result == {"ok": True}
    assert captured == {
        "user_input": "hello",
        "stream": False,
        "enabled_tool_names": ["calculator"],
        "model_id": "m1",
    }
