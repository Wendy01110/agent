import tools.registry as registry
import tools.math_python_tools as math_tools
import pytest


def test_calculator_tool(monkeypatch):
    class DummyMath:
        def run(self, _input):
            return "4"

    monkeypatch.setattr(math_tools.LLMMathChain, "from_llm", lambda llm, verbose=False: DummyMath())
    tools = registry.get_tools(llm=object())
    calculator = next(tool for tool in tools if tool.name == "calculator")

    result = calculator.invoke({"expression": "2+2"})
    assert "4" in str(result)


def test_python_tool_executes(monkeypatch):
    class DummyMath:
        def run(self, _input):
            return "0"

    monkeypatch.setattr(math_tools.LLMMathChain, "from_llm", lambda llm, verbose=False: DummyMath())
    tools = registry.get_tools(llm=object())
    python_tool = next(tool for tool in tools if tool.name == "python")

    result = python_tool.invoke({"code": "print(1+1)"})
    assert "2" in str(result)
