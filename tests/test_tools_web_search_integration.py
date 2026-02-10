import os
import pytest

from tools.web_search import WebSearchTool


@pytest.mark.skipif(
    os.getenv("RUN_TOOL_INTEGRATION") != "1",
    reason="Set RUN_TOOL_INTEGRATION=1 to run live tool calls.",
)
def test_web_search_integration():
    tool = WebSearchTool()
    results = tool.invoke({"query": "LangChain", "num_results": 10})
    print("web_search live results:", results)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert "title" in first and "url" in first
