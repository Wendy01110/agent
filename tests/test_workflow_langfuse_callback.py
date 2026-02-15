from workflow.langfuse_callback import build_langfuse_callback


def test_langfuse_callback_disabled(monkeypatch):
    monkeypatch.setenv("LANGFUSE_ENABLED", "0")
    assert build_langfuse_callback() is None


def test_langfuse_callback_enabled_with_kwargs(monkeypatch):
    captured = {}

    class DummyCallback:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setenv("LANGFUSE_ENABLED", "1")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.setattr("workflow.langfuse_callback._load_callback_class", lambda: DummyCallback)

    callback = build_langfuse_callback()
    assert isinstance(callback, DummyCallback)
    assert captured == {
        "public_key": "pk-test",
        "secret_key": "sk-test",
        "host": "https://cloud.langfuse.com",
    }
