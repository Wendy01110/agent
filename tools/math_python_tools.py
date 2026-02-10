"""Calculator and Python tools."""
from __future__ import annotations

from typing import Optional

from langchain_classic.chains.llm_math.base import LLMMathChain
from langchain_core.tools import BaseTool
from langchain_experimental.tools import PythonREPLTool
from pydantic import BaseModel, Field


class CalculatorArgs(BaseModel):
    expression: str = Field(..., description="Math expression or word problem.")


class CalculatorTool(BaseTool):
    name: str = "calculator"
    description: str = (
        "数学计算工具。"
        "输入：expression(数学表达式或文字题)。"
        "输出：计算结果字符串。"
        "示例：calculator(expression='200*365')。"
    )
    args_schema: Optional[type[BaseModel]] = CalculatorArgs

    def __init__(self, llm, **kwargs):
        super().__init__(**kwargs)
        self._chain = LLMMathChain.from_llm(llm=llm, verbose=False)

    def _run(self, *, expression: str) -> str:
        return self._chain.run(expression)


class PythonArgs(BaseModel):
    code: str = Field(..., description="Python code to execute, must print outputs.")


class PythonTool(BaseTool):
    name: str = "python"
    description: str = (
        "执行 Python 代码。"
        "输入：code(可执行 Python 代码，需自行 print 输出)。"
        "输出：代码执行的标准输出。"
        "示例：python(code='print(1+1)')。"
    )
    args_schema: Optional[type[BaseModel]] = PythonArgs

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._repl = PythonREPLTool()

    def _run(self, *, code: str) -> str:
        return self._repl.run(code)
