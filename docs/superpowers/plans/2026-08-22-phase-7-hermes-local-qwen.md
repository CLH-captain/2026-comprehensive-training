# Phase 7 Hermes 与本地 Qwen 实施计划

**目标：** 核验本机 Hermes Agent CN Desktop 0.7.0 的真实运行方式，通过稳定的程序化入口接入本地 Ollama/Qwen，并为后续 Tool API 与 Agent Web 闭环提供可测试的适配层。

**核验结论：** 桌面版内置 Hermes Runtime 0.19.0，Dashboard 实际监听 `127.0.0.1:9120`，对话使用内部网关而非设计草案中的 OpenAI `/v1` 接口；Runtime 官方提供 `--oneshot`、`chat --query --quiet`、模型/Provider 指定和会话恢复参数。因此后端使用 Hermes CLI Adapter，不修改 Hermes Core，也不依赖不稳定的桌面 WebSocket 私有协议。

### Task 1：配置与环境探测

**文件：**
- 修改 `backend/app/core/config.py`
- 修改 `.env.example`
- 新建 `scripts/start-ai-services.ps1`
- 新建 `scripts/check-ai-services.ps1`

- [x] 配置 Hermes Runtime 路径、Provider、模型、工作目录和调用超时。
- [x] 检查 Ollama `/api/tags`、Hermes Runtime 版本和 Dashboard 状态。
- [x] 启动脚本仅启动缺失的 Ollama/Hermes 服务，不影响 MySQL 和其他数据库。

### Task 2：Hermes CLI Adapter

**文件：**
- 新建 `backend/app/agent/__init__.py`
- 新建 `backend/app/agent/hermes.py`
- 新建 `backend/app/agent/schemas.py`

- [x] 以参数数组调用 Hermes Runtime，禁止 shell 拼接。
- [x] 支持基础单轮对话、模型/Provider 固定、超时、非零退出码和空响应分类。
- [x] 提供独立健康探测，区分 Runtime、Ollama 和模型配置状态。

### Task 3：后端基础接口与测试

**文件：**
- 新建 `backend/app/api/agent_runtime.py`
- 修改 `backend/app/main.py`
- 新建 `backend/tests/agent/test_hermes_client.py`
- 新建 `backend/tests/api/test_agent_runtime.py`

- [x] 新增登录后可访问的 `/api/agent/runtime` 状态接口。
- [x] 新增用于 Phase 7 验收的 `/api/agent/runtime/chat` 基础对话接口。
- [x] 使用假进程执行器覆盖成功、超时、启动失败、模型不可用和空响应。
- [x] 使用本机 Hermes + Qwen 完成一次最小真实冒烟测试。

### Task 4：文档与回归

**文件：**
- 修改 `docs/ROADMAP.md`
- 修改 `docs/API.md`
- 修改 `docs/TESTING.md`
- 修改 `README.md`

- [x] 记录 Hermes 0.7.0 / Runtime 0.19.0 的实际接口核验结论。
- [x] 写明本机 AI 服务启动、检查与故障提示。
- [x] 运行 Ruff、后端全量 pytest，并提交 Phase 7 里程碑。
