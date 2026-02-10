# Lessons Learned

- 遇到依赖导入错误时，先在目标环境中确认真实模块路径，再修改代码，避免反复试错。
- 对外部服务/模型调用类错误，先检查当前运行的 Python 环境与环境变量是否正确加载。
- LangChain 1.x 中 `Tool` 不在 `langchain.tools`，应从 `langchain_core.tools` 或 `langchain_classic.tools` 导入，修改前先在目标环境验证导入路径。
- 工具未被调用时优先检查 Agent 类型与模型能力匹配，必要时切换到 tool-calling agent 并开启解析错误处理。
