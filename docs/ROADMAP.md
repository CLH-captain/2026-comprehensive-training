# 项目开发任务清单

本路线图以 `docs/superpowers/specs/2026-08-22-szut-club-agent-design.md` 为设计基线。每个 Phase 开始前编写独立实施计划，完成后运行本阶段测试和既有回归测试，再进入下一阶段。

## Phase 1：项目初始化

- [x] 建立根目录规范、环境变量模板和本机环境检查脚本。
- [x] 建立 FastAPI 最小可启动应用、配置系统和健康检查测试。
- [x] 建立 Vue 3 + TypeScript + Vite 工程、API Client 和启动状态页。
- [x] 编写 Windows 本机 MySQL/Ollama/Hermes 启动说明。

## Phase 2：数据库

- [x] 建立 SQLAlchemy Base、Session 和测试库隔离保护。
- [x] 实现 18 张业务/认证表及关系、枚举、约束和索引。
- [x] 创建首个 Alembic 迁移并在开发库、测试库验证升级/降级。
- [x] 编写 Model、约束、外键和迁移测试。

## Phase 3：仿真数据集

- [x] 实现固定种子配置、学院偏好和分布模型。
- [x] 生成基础字典、学生、社团、成员、活动、报名和签到。
- [x] 支持 MySQL Seed、CSV 导出和安全 `--reset`。
- [x] 生成并验证 `data_quality_report.json`。

## Phase 4：Statistics Service

- [x] 实现 overview、社团/活动排行、趋势和分布。
- [x] 实现 student summary、club summary 和统一活跃度。
- [x] 对固定数据集建立 SQL 基准答案和 100% 确定性统计测试。

## Phase 5：FastAPI 业务接口

- [x] 实现 JWT、注销、初始管理员和 RBAC。
- [x] 实现基础字典、学生、社团、活动、报名、签到 API。
- [x] 实现 Statistics API、分页、统一错误和 request_id。
- [x] 完成 admin、club_manager、student 权限矩阵 API 测试。

## Phase 6：Vue 管理与统计前端

- [x] 实现登录、权限路由、桌面端会话布局、学期和校区上下文。
- [x] 实现 Dashboard 4 个指标卡与 Analytics 7 张 ECharts 图表。
- [x] 实现学生、社团、活动、报名、签到管理页。
- [x] 实现 Analytics、官方校园视觉素材和前端自动化测试。

## Phase 7：Hermes 与本地 Qwen

- [x] 核验 Hermes Agent CN Desktop 0.7.0 的实际 API/插件接口。
- [x] 启动 Ollama 并验证 `qwen3.5-4b-64k:latest` 的 65536 上下文配置。
- [x] 建立 FastAPI Hermes Adapter 并完成基础对话测试。

## Phase 8：Hermes Plugin 与内部 Tool API

- [x] 实现 Agent Context Token 和 `X-Agent-Internal-Key` 验证。
- [x] 实现 7 个 Internal Tool API，全部复用 Statistics/Service。
- [x] 实现项目级 Hermes Plugin、严格 Tool Schema 和权限测试。

## Phase 9：Agent Web 闭环

- [x] 实现会话、消息和 `/api/agent/chat`。
- [x] 实现 Agent 前端、快捷问题、结构化数据和 Chart Specification。
- [x] 完成 Vue → FastAPI → Hermes → Tool → MySQL 端到端测试。

## Phase 10：DeepSeek Fallback

- [x] 配置 DeepSeek Provider 和可恢复错误分类。
- [x] 实现脱敏聚合上下文和个人明细禁用云端降级。
- [ ] 停止 Ollama 后完成 Fallback 与日志验证。

## Phase 11：加固与验收

- [x] 完善结构化日志、异常、超时、空状态、可访问性和 UI。
- [x] 完成 40 问 Agent 测试集和统计准确性对比。
- [x] 运行后端、前端、数据和本地 HTTP 冒烟回归。
- [x] 完成 README、API、TESTING 和验收记录。

## 后置工作

- 实训报告和答辩 PPT 在系统验收后单独制作。
- Phase 12 的 MCP、Skills、Excel、自动报告等不属于当前 MVP。
- 本课程项目不做移动端适配；保留必要认证与数据权限，不追加生产级限流和复杂审计。
