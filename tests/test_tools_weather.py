from tools.weather import WeatherTool


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_weather_formats_output(monkeypatch):
    payload = {
        "current_condition": [
            {
                "temp_C": "10",
                "temp_F": "50",
                "weatherDesc": [{"value": "Cloudy"}],
                "FeelsLikeC": "8",
                "humidity": "60",
                "windspeedKmph": "12",
            }
        ],
        "nearest_area": [{"areaName": [{"value": "Beijing"}]}],
        "weather": [
            {
                "date": "2025-01-01",
                "maxtempC": "12",
                "mintempC": "5",
                "avgtempC": "8",
                "hourly": [
                    {
                        "time": "0",
                        "tempC": "6",
                        "FeelsLikeC": "4",
                        "weatherDesc": [{"value": "Sunny"}],
                    }
                ],
            }
        ],
    }

    def fake_get(*args, **kwargs):
        return DummyResponse(payload)

    monkeypatch.setattr("requests.get", fake_get)
    tool = WeatherTool()
    result = tool.invoke({"city": "Beijing", "days": 2, "hourly": True})
    print("weather mock result:", result)

    assert "Beijing" in result
    assert "Cloudy" in result
    assert "10°C/50°F" in result
    assert "2025-01-01" in result
    assert "Hourly:" in result
    assert "00:00" in result
