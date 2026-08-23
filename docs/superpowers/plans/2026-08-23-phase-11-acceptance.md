# Phase 11 Acceptance Implementation Plan

> **For agentic workers:** Execute inline task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 完成课程项目范围内的运行日志、Agent 验收集、错误体验和最终回归记录。

**Architecture:** FastAPI 以 JSON 记录请求 ID、状态、耗时和安全的 Agent 来源，不记录提示词、密钥或完整个人数据。40 个验收问题以固定统计口径映射到既有 Statistics Service 和 7 个 Tool，用自动测试验证题集完整性与基准数据。

**Tech Stack:** FastAPI、Python logging、pytest、Vue 3、Vite。

## Global Constraints

- 不记录密码、JWT、API Key、内部 Key、提示词或隐藏推理。
- 不再进行 DeepSeek 云端调用。
- 不做移动端适配、生产级限流或复杂审计。

---

### Task 1: Structured request and Agent outcome logs

- [x] Add a JSON formatter and configure it once per application process.
- [x] Log request ID, method, path, status and duration; log Agent source/model/fallback without prompt content.
- [x] Add formatter and agent logging tests.

### Task 2: Acceptance question set

- [x] Add 40 fixed aggregate questions mapped to allowed statistics capabilities.
- [x] Test question count, unique IDs, valid tool names and baseline overview assertions.

### Task 3: Regression and handoff

- [x] Run backend, frontend and HTTP smoke checks.
- [x] Update API, testing, roadmap and README records.
- [x] Commit and synchronize after all local acceptance passes.
