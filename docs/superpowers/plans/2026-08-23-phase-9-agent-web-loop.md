# Phase 9 Agent Web Loop Implementation Plan

> **For agentic workers:** Execute inline task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 完成可保存会话、调用 Hermes 统计 Tool、返回结构化数据并在 Vue 中展示文字/表格/图表的 Agent 闭环。

**Architecture:** Vue 只调用 FastAPI。FastAPI 保存会话和消息、签发短期 Context Token、调用 Hermes CLI；Hermes 插件调用 Internal Tool API。插件把本次 Tool 名称、参数和结果写入仅本次子进程可见的临时 trace，Adapter 读取后立即删除，并把最终回答与脱敏 Tool 摘要持久化。

**Tech Stack:** FastAPI、SQLAlchemy Core、Hermes Runtime、Vue 3、TypeScript、Element Plus、ECharts、Vitest。

## Global Constraints

- 不返回或保存模型隐藏推理。
- 所有确定性数字必须来自已注册 Tool。
- Chart Specification 只允许 `bar`、`line`、`pie`，不执行模型 JavaScript。
- 学生只能访问自己的会话；社团负责人和学生仍受 Phase 8 数据范围限制。
- 不做移动端适配，不增加生产级限流或复杂审计。

---

### Task 1：Hermes Tool Trace

**Files:** `backend/app/agent/hermes.py`、`backend/app/agent/schemas.py`、`hermes_plugin/szut-club-statistics/tools.py`、相关测试。

- [x] Hermes 子进程固定加载 `szut_club_statistics` Toolset。
- [x] 为每次调用创建独立 trace 文件，并通过环境变量传给插件。
- [x] 插件记录 Tool 名称、参数和结构化结果；Adapter 解析后立即删除临时文件。
- [x] 覆盖无 Tool、单 Tool、损坏 trace 和清理测试。

### Task 2：会话、消息与 Chat API

**Files:** `backend/app/services/agent.py`、`backend/app/api/agent.py`、`backend/app/schemas/agent.py`、`backend/app/main.py`、API 测试。

- [x] 实现会话列表、会话消息和删除本人会话。
- [x] 实现 `POST /api/agent/chat`，新建或校验会话、保存用户消息、调用 Hermes、保存最终回答。
- [x] 只在数据库保存 Tool 名称、参数摘要和模型名，不保存隐藏推理或临时内部凭据。
- [x] 从 Tool 数据生成受控表格和 bar/line/pie Chart Specification。

### Task 3：Agent 前端

**Files:** `frontend/src/views/AgentView.vue`、`frontend/src/api/agent.ts`、`frontend/src/types/agent.ts`、路由与页面导航、前端测试。

- [x] 实现会话册、欢迎区、快捷问题、消息流和输入区。
- [x] 展示模型、Tool 数据凭证、结构化表格和 ECharts 图表。
- [x] 实现发送中、空状态、失败重试和会话切换。
- [x] 将“智能助手”加入现有桌面端导航，不改移动端。

### Task 4：闭环与验收

- [x] 自动化验证 Vue API 类型、会话权限、消息持久化、Tool Trace 和 Chart Specification。
- [x] 使用本机 Hermes/Qwen 完成至少一个真实统计问题的端到端调用。
- [x] 运行后端、前端、构建和差异检查，更新 ROADMAP、API、TESTING、README。
- [x] 提交 Phase 9，并安全同步 GitHub；Gitea 在认证可用时同步。
