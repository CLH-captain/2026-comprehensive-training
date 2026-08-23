# DeepSeek Fallback Implementation Plan

> **For agentic workers:** Execute inline task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在本地 Hermes/Ollama 可恢复失败时，为管理员的聚合统计问题提供受控 DeepSeek 备用回答。

**Architecture:** FastAPI 先调用 Hermes；仅对运行时缺失、启动失败、连接失败、超时和空响应执行一次备用尝试。备用调用只接收用户问题、筛选条件和 `StatisticsService.dashboard()` 产生的聚合快照；学生、社团负责人和个人明细关键词均禁用云端备用。

**Tech Stack:** FastAPI、httpx、StatisticsService、pytest。

## Global Constraints

- 不上传 JWT、密码、Key、数据库结构、原始个人记录或隐藏推理。
- 不修改 Hermes Core，不增加移动端功能或生产级审计。
- 每次真实云端验收只发送一个聚合问题。

---

### Task 1: Fallback client and policy

**Files:** `backend/app/agent/deepseek.py`, `backend/app/agent/fallback.py`, `backend/tests/agent/test_deepseek.py`.

- [ ] Add a small OpenAI-compatible DeepSeek client with safe timeout and error mapping.
- [ ] Add recoverable-error classification and a policy which blocks non-admin and personal-detail requests.
- [ ] Verify request payload contains only an aggregate snapshot and no secret headers beyond the outbound API authorization.

### Task 2: Agent API orchestration

**Files:** `backend/app/api/agent.py`, `backend/app/schemas/agent.py`, `backend/tests/api/test_agent.py`.

- [ ] Retry Hermes once only for recoverable failures, then call fallback when policy permits.
- [ ] Build the aggregate snapshot through `StatisticsService.dashboard()` using term/campus filters.
- [ ] Return and persist the selected model without exposing fallback prompt or credentials.

### Task 3: Verification and documentation

**Files:** `docs/ROADMAP.md`, `docs/API.md`, `docs/TESTING.md`, `README.md`.

- [ ] Run mock policy/client/API tests and the complete backend regression suite.
- [ ] Run one real aggregate fallback request after temporarily making the local Hermes call unavailable; restore local service configuration immediately.
- [ ] Record result, update roadmap, commit and synchronize both remotes.
