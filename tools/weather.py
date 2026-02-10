"""Weather tool using wttr.in free endpoint."""
from __future__ import annotations

from typing import Dict, Any, Optional

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


WTTR_URL = "https://wttr.in"


def _format_weather(payload: Dict[str, Any]) -> str:
    current = (payload.get("current_condition") or [{}])[0]
    area = (payload.get("nearest_area") or [{}])[0]
    area_name = (area.get("areaName") or [{}])[0].get("value", "")
    temp_c = current.get("temp_C", "")
    temp_f = current.get("temp_F", "")
    weather_desc = (current.get("weatherDesc") or [{}])[0].get("value", "")
    feels_like_c = current.get("FeelsLikeC", "")
    humidity = current.get("humidity", "")
    wind_kph = current.get("windspeedKmph", "")

    return (
        f"{area_name} | {weather_desc} | "
        f"{temp_c}°C/{temp_f}°F (feels {feels_like_c}°C) | "
        f"humidity {humidity}% | wind {wind_kph} km/h"
    )


class WeatherArgs(BaseModel):
    city: str = Field(..., description="City English name.")
    days: int = Field(1, description="Number of days to return (1-3 recommended).")
    hourly: bool = Field(False, description="Whether to include today's hourly forecast.")


class WeatherTool(BaseTool):
    name: str = "weather"
    description: str = (
        "获取城市天气（当前 + 可选多日/分时段）。"
        "输入：city(城市的英文名), days(天数, 建议1-3), hourly(是否包含当天分时段)。"
        "输出：多行字符串，首行为当前天气，其次可含Hourly分时段，最后为每日预报。"
        "示例：weather(city='Beijing', days=3, hourly=True)。"
        "适用：需要即时天气与短期预报的场景。"
        "城市名需要使用英文，例如 Beijing, Shanghai, New York。不支持中文。"
    )
    args_schema: Optional[type[BaseModel]] = WeatherArgs

    def _run(self, *, city: str, days: int = 1, hourly: bool = False) -> str:
        url = f"{WTTR_URL}/{city}"
        response = requests.get(
            url,
            params={"format": "j1", "num_of_days": days},
            timeout=30,
            proxies={"http": None, "https": None},
        )
        response.raise_for_status()
        data = response.json()

        if days <= 1 and not hourly:
            return _format_weather(data)

        forecast_days = data.get("weather", [])[:days]
        lines = [_format_weather(data)]
        if hourly:
            today = (data.get("weather") or [{}])[0]
            hourly_items = today.get("hourly", []) or []
            hourly_lines = []
            for item in hourly_items:
                time_raw = item.get("time", "")
                if str(time_raw).isdigit():
                    padded = str(time_raw).zfill(4)
                    hour = int(padded[:-2])
                    minute = int(padded[-2:])
                    time_str = f"{hour:02d}:{minute:02d}"
                else:
                    time_str = str(time_raw)
                temp_c = item.get("tempC", "")
                desc = (item.get("weatherDesc") or [{}])[0].get("value", "").strip()
                feels_c = item.get("FeelsLikeC", "")
                hourly_lines.append(
                    f"{time_str} | {desc} | {temp_c}°C (feels {feels_c}°C)"
                )
            if hourly_lines:
                lines.append("Hourly:")
                lines.extend(hourly_lines)
        for day in forecast_days:
            date = day.get("date", "")
            maxtemp_c = day.get("maxtempC", "")
            mintemp_c = day.get("mintempC", "")
            avgtemp_c = day.get("avgtempC", "")
            desc = ((day.get("hourly") or [{}])[0].get("weatherDesc") or [{}])[0].get(
                "value", ""
            )
            lines.append(
                f"{date} | {desc} | {mintemp_c}°C~{maxtemp_c}°C (avg {avgtemp_c}°C)"
            )
        return "\n".join(lines)
