import os

import tools.bocha_search as bocha_module
from tools.bocha_search import BochaSearchTool


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_bocha_search_parses_results(monkeypatch):
    monkeypatch.setenv("BOCHA_API_KEY", "test-key")

    payload = {
        "data": {
            "webPages": {
                "value": [
                    {
                        "name": "Result A",
                        "url": "https://example.com/a",
                        "summary": "Snippet A",
                    }
                ]
            }
        }
    }

    def fake_post(*args, **kwargs):
        return DummyResponse(payload)

    monkeypatch.setattr(bocha_module.requests, "post", fake_post)
    tool = BochaSearchTool()
    results = tool.invoke({"query": "test", "count": 1})
    print("bocha_search mock results:", results)

    assert len(results) == 1
    assert results[0]["title"] == "Result A"
    assert results[0]["url"] == "https://example.com/a"
    assert results[0]["snippet"] == "Snippet A"
