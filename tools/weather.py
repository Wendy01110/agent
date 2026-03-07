"""Weather tool powered by AMap Weather API."""
from __future__ import annotations

import os
from typing import Dict, Any, Optional

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
AMAP_DISTRICT_URL = "https://restapi.amap.com/v3/config/district"


def _request_json(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Send HTTP request and parse JSON payload."""
    response = requests.get(
        url,
        params=params,
        timeout=30,
        proxies={"http": None, "https": None},
    )
    response.raise_for_status()
    data = response.json()
    if str(data.get("status")) != "1":
        raise ValueError(data.get("info", "AMap API request failed"))
    return data


def _resolve_adcode(city: str, key: str) -> str:
    """Resolve city keyword to adcode, pass through when already adcode."""
    clean_city = city.strip()
    if clean_city.isdigit() and len(clean_city) == 6:
        return clean_city

    data = _request_json(
        AMAP_DISTRICT_URL,
        {"keywords": clean_city, "key": key, "subdistrict": 0, "extensions": "base"},
    )
    districts = data.get("districts") or []
    if not districts:
        raise ValueError(f"未找到城市对应 adcode: {city}")
    adcode = str(districts[0].get("adcode", "")).strip()
    if not adcode:
        raise ValueError(f"未找到城市对应 adcode: {city}")
    return adcode


def _format_live(data: Dict[str, Any]) -> str:
    """Format AMap current weather payload."""
    live = (data.get("lives") or [{}])[0]
    province = live.get("province", "")
    city = live.get("city", "")
    weather = live.get("weather", "")
    temperature = live.get("temperature", "")
    winddirection = live.get("winddirection", "")
    windpower = live.get("windpower", "")
    humidity = live.get("humidity", "")
    reporttime = live.get("reporttime", "")
    location = city or province
    return (
        f"{location} | {weather} | {temperature}°C | "
        f"湿度 {humidity}% | 风向 {winddirection} 风力 {windpower}级 | 更新时间 {reporttime}"
    )


def _format_forecast(data: Dict[str, Any], days: int) -> list[str]:
    """Format AMap forecast payload."""
    forecast = (data.get("forecasts") or [{}])[0]
    casts = (forecast.get("casts") or [])[:days]
    lines = []
    for item in casts:
        date = item.get("date", "")
        dayweather = item.get("dayweather", "")
        nightweather = item.get("nightweather", "")
        daytemp = item.get("daytemp", "")
        nighttemp = item.get("nighttemp", "")
        daywind = item.get("daywind", "")
        nightwind = item.get("nightwind", "")
        daypower = item.get("daypower", "")
        nightpower = item.get("nightpower", "")
        lines.append(
            f"{date} | 白天{dayweather} {daytemp}°C {daywind}风{daypower}级 | "
            f"夜间{nightweather} {nighttemp}°C {nightwind}风{nightpower}级"
        )
    return lines


class WeatherArgs(BaseModel):
    city: str = Field(..., description="城市名（中文/英文）或 adcode（6位行政区编码）。")
    days: int = Field(1, description="返回天数，1-4。>1 时返回未来预报。")
    hourly: bool = Field(False, description="兼容参数；高德不提供小时级预报。")


class WeatherTool(BaseTool):
    name: str = "weather"
    description: str = (
        "通过高德天气 API 获取天气。"
        "输入：city(城市名或 adcode), days(1-4), hourly(兼容参数)。"
        "输出：字符串，首行为实时天气，必要时附加未来天气预报。"
        "示例：weather(city='北京', days=3, hourly=False)。"
        "说明：需要 AMAP_API_KEY 环境变量。"
    )
    args_schema: Optional[type[BaseModel]] = WeatherArgs

    def _run(self, *, city: str, days: int = 1, hourly: bool = False) -> str:
        api_key = os.getenv("AMAP_API_KEY") or os.getenv("GAODE_API_KEY")
        if not api_key:
            raise ValueError("AMAP_API_KEY is required for weather")

        query_days = max(1, min(days, 4))
        adcode = _resolve_adcode(city, api_key)

        live_data = _request_json(
            AMAP_WEATHER_URL,
            {"city": adcode, "key": api_key, "extensions": "base", "output": "JSON"},
        )
        lines = [_format_live(live_data)]

        if query_days > 1 or hourly:
            forecast_data = _request_json(
                AMAP_WEATHER_URL,
                {"city": adcode, "key": api_key, "extensions": "all", "output": "JSON"},
            )
            lines.extend(_format_forecast(forecast_data, query_days))
        return "\n".join(lines)
