import os
import pytest

from tools.weather import WeatherTool


@pytest.mark.skipif(
    os.getenv("RUN_TOOL_INTEGRATION") != "1",
    reason="Set RUN_TOOL_INTEGRATION=1 to run live tool calls.",
)
def test_weather_integration():
    tool = WeatherTool()
    result = tool.invoke({"city": "Beijing", "days": 3, "hourly": True})
    print("weather live result:", result)
    assert isinstance(result, str)
    assert result
    assert "°C" in result
