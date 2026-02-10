"""Analyst agent: synthesizes final response from tool outputs."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate
from prompt.analyst_prompt import AnalystPrompt


class AnalystAgent:
    """Summarize results, keep structure, and answer the user clearly."""

    def __init__(self, llm):
        self.llm = llm
        system_text, human_text = AnalystPrompt.build()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_text),
                ("human", human_text),
            ]
        )

    @staticmethod
    def _format_outputs(intermediate_steps: List[Any]) -> str:
        lines = []
        for step in intermediate_steps:
            action, observation = step
            tool = getattr(action, "tool", "")
            tool_input = getattr(action, "tool_input", "")
            lines.append(f"Tool: {tool}\nInput: {tool_input}\nOutput: {observation}\n")
        return "\n".join(lines) if lines else "(no tool outputs)"

    def summarize(
        self,
        user_input: str,
        plan: str,
        result: Dict[str, Any],
        tool_desc: str,
        now: str,
        callbacks=None,
    ) -> str:
        """Return final response synthesized by the analyst."""
        outputs = self._format_outputs(result.get("intermediate_steps", []))
        chain = self.prompt | self.llm
        config = {"callbacks": callbacks} if callbacks else None
        return chain.invoke(
            {
                "input": user_input,
                "plan": plan,
                "outputs": outputs,
                "tool_desc": tool_desc,
                "now": now,
            },
            config=config,
        ).content
