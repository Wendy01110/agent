import os
import pytest

from tools.bocha_search import BochaSearchTool


@pytest.mark.skipif(
    os.getenv("RUN_TOOL_INTEGRATION") != "1" or not os.getenv("BOCHA_API_KEY"),
    reason="Set RUN_TOOL_INTEGRATION=1 and BOCHA_API_KEY to run live tool calls.",
)
def test_bocha_search_integration():
    tool = BochaSearchTool()
    results = tool.invoke({"query": "阿里巴巴2024年的ESG报告", "count": 10})
    print("bocha_search live results:", results)
    assert isinstance(results, list)
