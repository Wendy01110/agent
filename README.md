# 多 Agent 智能体系统（LangChain）

本项目实现一个模块化多 Agent 体系，核心能力包括任务规划、工具自动调用与结果整合。
当前场景为“日常智能助理”，支持天气查询、数学计算、代码执行与搜索检索等。

## 特性

- 多 Agent 协作：Planner / Executor / Analyst 职责清晰
- 工具路由：统一注册与语义化工具描述
- 流式输出与工具调用日志
- 可扩展架构：便于加入更多工具与工作流

## 目录结构

```
config/         # LLM 与环境配置
tools/          # 外部能力封装（搜索/天气/计算/Python）
agents/         # 规划/执行/分析
workflow/       # 多 Agent 调度编排
prompt/         # Prompt 类定义
tests/          # 测试用例
main.py         # 启动入口
```

## 环境要求

- Python 3.12
- 依赖安装：

```bash
/opt/miniconda3/envs/agent/bin/python -m pip install -r requirements.txt
```

## API 配置（.env）

在项目根目录创建 `.env`，至少包含以下内容：

```env
# 火山方舟（豆包）
ARK_API_KEY=your_ark_api_key
ARK_MODEL=your_endpoint_id
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Bocha 搜索
BOCHA_API_KEY=your_bocha_api_key
```

说明：

- LLM 默认读取 `ARK_*` 配置。
- 为兼容旧配置，代码仍支持读取 `HUOSHAN_API_KEY` 作为备用。
- Bocha 搜索工具需要 `BOCHA_API_KEY`，否则会报错。
- Langfuse 可选开启，用于查看 LLM/Tool 调用链路与 token 用量。

Langfuse 配置示例：

```env
LANGFUSE_ENABLED=1
LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

说明：

- `LANGFUSE_ENABLED=1` 时，`workflow/flow.py` 会自动注入 Langfuse callback。
- 未安装 `langfuse` 或配置缺失时，会打印提示并继续运行，不影响主流程。

`.env` 模板见：`.env.example`

## 运行

### 交互式对话

```bash
python main.py
```

命令：

- `/reset` 清空上下文
- `/exit` 退出

### 单次执行

```bash
main.py "查询北京天气并计算每月存200一年是多少"
```

## 流式输出与工具日志

默认开启流式输出与工具调用日志：

- `[PLANNER]` / `[EXECUTOR]` / `[ANALYST]` 标签
- `[TOOL START]` / `[TOOL END]` 日志

可在 `workflow/flow.py` 里关闭 `stream`。

## 测试

```bash
python -m pytest -q
```

集成测试（会触发外网调用）：

```bash
RUN_TOOL_INTEGRATION=1 python -m pytest -q
```

LLM 集成测试：

```bash
RUN_LLM_INTEGRATION=1 python -m pytest -q tests/test_llm_config.py
```

## 备注

如需新增工具，请在 `tools/` 下创建，并在 `tools/registry.py` 注册。
如需调整 Prompt，请修改 `prompt/` 目录下对应类。
