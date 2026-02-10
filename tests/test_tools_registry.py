from types import SimpleNamespace

import tools.registry as registry
import tools.math_python_tools as math_tools


def test_registry_returns_tools(monkeypatch):
    dummy_chain = SimpleNamespace(run=lambda x: "0")
    monkeypatch.setattr(math_tools.LLMMathChain, "from_llm", lambda llm, verbose=False: dummy_chain)

    tools = registry.get_tools(llm=object())
    print("registry tools:", [tool.name for tool in tools])
    names = {tool.name for tool in tools}

    assert {"calculator", "python", "web_search", "bocha_search", "weather"}.issubset(
        names
    )
