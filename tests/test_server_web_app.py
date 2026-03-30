from server.web_app import AgentHTTPRequestHandler


def test_compose_input_with_history():
    history = [
        {"user": "你好", "assistant": "你好，我在。"},
        {"user": "北京天气", "assistant": "今天晴。"},
    ]
    composed = AgentHTTPRequestHandler._compose_input(history, "继续给出穿衣建议")
    assert "用户：你好" in composed
    assert "助手：今天晴。" in composed
    assert composed.endswith("用户：继续给出穿衣建议")


def test_compose_input_without_valid_history():
    composed = AgentHTTPRequestHandler._compose_input([{"bad": "x"}], "单轮问题")
    assert composed == "单轮问题"
