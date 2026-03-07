import os
import pytest

from tools.weather import WeatherTool


@pytest.mark.skipif(
    os.getenv("RUN_TOOL_INTEGRATION") != "1" or not os.getenv("AMAP_API_KEY"),
    reason="Set RUN_TOOL_INTEGRATION=1 and AMAP_API_KEY to run live tool calls.",
)
def test_weather_integration():
    tool = WeatherTool()
    result = tool.invoke({"city": "北京", "days": 3, "hourly": False})
    print("weather live result:", result)
    assert isinstance(result, str)
    assert result
    assert "°C" in result
