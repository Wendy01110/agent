"""Planner agent: decomposes user goals into actionable steps."""
from __future__ import annotations

from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from prompt.planner_prompt import PlannerPrompt


class PlannerAgent:
    """Generate a concise, tool-aware plan for the request."""

    def __init__(self, llm):
        self.llm = llm
        system_text, human_text = PlannerPrompt.build()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_text),
                ("human", human_text),
            ]
        )

    def plan(self, user_input: str, tool_desc: str, now: str, callbacks=None) -> str:
        """Return a short plan string."""
        chain = self.prompt | self.llm
        config = {"callbacks": callbacks} if callbacks else None
        return chain.invoke(
            {"input": user_input, "tool_desc": tool_desc, "now": now}, config=config
        ).content
