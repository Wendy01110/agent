"""Bocha web search tool."""
from __future__ import annotations

import os
from typing import List, Dict, Optional

import requests
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


BOCHA_URL = "https://api.bocha.cn/v1/web-search"


class BochaSearchArgs(BaseModel):
    query: str = Field(..., description="Search keywords.")
    summary: bool = Field(True, description="Whether to request summaries from Bocha.")
    freshness: str = Field(
        "noLimit",
        description='Time range filter, e.g. "noLimit", "day", "week", "month", "year".',
    )
    count: int = Field(10, description="Max number of results to return.")


def _normalize_results(results: List[Dict[str, object]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for item in results:
        title = str(item.get("name", "") or item.get("title", ""))
        url = str(item.get("url", ""))
        snippet = str(item.get("summary", "") or item.get("snippet", ""))
        normalized.append({"title": title, "url": url, "snippet": snippet})
    return normalized


class BochaSearchTool(BaseTool):
    name: str = "bocha_search"
    description: str = (
        "通过 Bocha API 进行网页搜索并返回结构化结果。"
        "输入：query(关键词), summary(是否返回摘要), freshness(时间范围), count(结果数)。"
        "输出：List[{'title': 标题, 'url': 链接, 'snippet': 摘要}]。"
        "示例：bocha_search(query='阿里巴巴2024 ESG报告', summary=True, freshness='year', count=10)。"
        "说明：需要 BOCHA_API_KEY 环境变量。"
    )
    args_schema: Optional[type[BaseModel]] = BochaSearchArgs

    def _run(
        self,
        *,
        query: str,
        summary: bool = True,
        freshness: str = "noLimit",
        count: int = 10,
    ) -> List[Dict[str, str]]:
        api_key = os.getenv("BOCHA_API_KEY")
        if not api_key:
            raise ValueError("BOCHA_API_KEY is required for bocha_search")

        payload = {
            "query": query,
            "summary": summary,
            "freshness": freshness,
            "count": count,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(BOCHA_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()
        data_block = data.get("data", {})
        web_pages = data_block.get("webPages", {}).get("value", [])
        results = web_pages or data_block.get("results", []) or data.get("results", [])
        return _normalize_results(results)
