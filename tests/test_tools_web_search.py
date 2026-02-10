import tools.web_search as web_search_module
from tools.web_search import WebSearchTool


def test_web_search_parses_results(monkeypatch):
    def fake_search(*args, **kwargs):
        return [
            {"title": "Result A", "url": "https://example.com/a", "abstract": "Snippet A"},
            {"title": "Result B", "url": "https://example.com/b", "abstract": "Snippet B"},
        ]

    monkeypatch.setattr(web_search_module, "baidu_search", fake_search)
    tool = WebSearchTool()
    results = tool.invoke({"query": "test", "num_results": 2})
    print("web_search mock results:", results)

    assert len(results) == 2
    assert results[0]["title"] == "Result A"
    assert results[0]["url"] == "https://example.com/a"
    assert results[0]["snippet"] == "Snippet A"
