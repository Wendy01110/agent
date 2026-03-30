# Lessons Learned

- 遇到依赖导入错误时，先在目标环境中确认真实模块路径，再修改代码，避免反复试错。
- 对外部服务/模型调用类错误，先检查当前运行的 Python 环境与环境变量是否正确加载。
- LangChain 1.x 中 `Tool` 不在 `langchain.tools`，应从 `langchain_core.tools` 或 `langchain_classic.tools` 导入，修改前先在目标环境验证导入路径。
- 工具未被调用时优先检查 Agent 类型与模型能力匹配，必要时切换到 tool-calling agent 并开启解析错误处理。
- 环境变量命名必须在代码、README、.env.example 三处一致；变更命名时优先保留兼容回退，避免已有部署因重命名中断。
- 外部 API 源切换（如 wttr.in -> 高德）时，应保持工具入参尽量兼容，并同时更新单测、集成测试和环境变量说明。
- 工作流从函数式入口重构为类时，应保留兼容包装函数，先稳住已有 CLI/API 调用，再逐步迁移到 class 接口。
- 多 Agent Web 可观测性应统一输出结构化 trace（agent 输入/输出/推理、tool I/O）并落 JSONL，同时挂 Langfuse callback，避免只靠控制台流式日志。
- 模型切换应在 `config/model.py` 统一定义（id/label/default），业务层仅透传 `model_id`，避免在 workflow/server 前端各自维护模型清单。
- 流式 NDJSON 前端必须识别显式结束事件并主动停止 reader；仅依赖连接自然关闭会导致“发送中”状态卡住。
