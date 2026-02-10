"""Baidu search tool based on the baidusearch package."""
from __future__ import annotations

from typing import List, Dict, Optional

from baidusearch.baidusearch import search as baidu_search
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class WebSearchArgs(BaseModel):
    query: str = Field(..., description="Search keywords.")
    num_results: int = Field(5, description="Max number of results to return.")


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "使用百度搜索获取网页结果，返回结构化列表。"
        "输入：query(关键词), num_results(结果数)。"
        "输出：List[{'title': 标题, 'url': 链接, 'snippet': 摘要}]。"
        "示例：web_search(query='LangChain 多 Agent', num_results=3)。"
        "适用：需要网页检索与参考链接的任务。"
    )
    args_schema: Optional[type[BaseModel]] = WebSearchArgs

    def _run(self, *, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        results = baidu_search(query, num_results=num_results)
        normalized: List[Dict[str, str]] = []
        for item in results or []:
            title = item.get("title", "")
            url = item.get("url", "")
            snippet = item.get("abstract", "") or item.get("snippet", "")
            normalized.append({"title": title, "url": url, "snippet": snippet})
        return normalized
