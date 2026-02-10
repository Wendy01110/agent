"""Tool executor agent: uses LLM tool-calling to complete tasks."""
from __future__ import annotations

from typing import Any, Dict, List

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from prompt.executor_prompt import ExecutorPrompt


class ToolExecutorAgent:
    """Execute a plan by selecting and calling tools via LangChain agents."""

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

        system_text, human_text = ExecutorPrompt.build()
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_text),
                ("human", human_text),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            return_intermediate_steps=True,
            verbose=False,
            handle_parsing_errors=True,
        )

    def execute(
        self, user_input: str, plan: str, now: str, callbacks=None
    ) -> Dict[str, Any]:
        """Return the agent result and intermediate tool outputs."""
        config = {"callbacks": callbacks} if callbacks else None
        return self.executor.invoke(
            {"input": user_input, "plan": plan, "now": now}, config=config
        )
