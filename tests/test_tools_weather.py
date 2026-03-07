from tools.weather import WeatherTool


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_weather_formats_output(monkeypatch):
    district_payload = {
        "status": "1",
        "districts": [{"name": "北京市", "adcode": "110000"}],
    }
    live_payload = {
        "status": "1",
        "lives": [
            {
                "province": "北京",
                "city": "北京市",
                "weather": "多云",
                "temperature": "10",
                "winddirection": "北",
                "windpower": "3",
                "humidity": "60",
                "reporttime": "2025-01-01 10:00:00",
            }
        ],
    }
    forecast_payload = {
        "status": "1",
        "forecasts": [
            {
                "city": "北京市",
                "casts": [
                    {
                        "date": "2025-01-01",
                        "dayweather": "晴",
                        "nightweather": "多云",
                        "daytemp": "12",
                        "nighttemp": "5",
                        "daywind": "北",
                        "nightwind": "北",
                        "daypower": "3",
                        "nightpower": "2",
                    }
                ],
            }
        ],
    }

    def fake_get(*args, **kwargs):
        url = args[0]
        if url.endswith("/district"):
            return DummyResponse(district_payload)
        if kwargs.get("params", {}).get("extensions") == "all":
            return DummyResponse(forecast_payload)
        return DummyResponse(live_payload)

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setenv("AMAP_API_KEY", "test-key")
    tool = WeatherTool()
    result = tool.invoke({"city": "北京", "days": 2, "hourly": True})
    print("weather mock result:", result)

    assert "北京市" in result
    assert "多云" in result
    assert "10°C" in result
    assert "2025-01-01" in result
    assert "白天晴" in result
