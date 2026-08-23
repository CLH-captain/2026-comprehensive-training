# 测试与验收

## 安全边界

- 后端数据测试只允许连接 `szut_club_agent_test`。
- 测试入口会调用 `assert_test_database_url`，数据库名称不符合要求时立即终止。
- 固定种子基线为 3000 名学生、45 个社团、324 场活动、22299 条报名和 19979 条签到。

## 常用命令

在 `backend` 目录运行：

```powershell
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\ruff.exe check app tests
```

在 `frontend` 目录运行：

```powershell
pnpm test -- --run
pnpm build
```

## Statistics Service 基准

`backend/tests/statistics/benchmark_queries.py` 使用独立原始 SQL 计算总览、月度趋势、四类排行和三类分布。`test_benchmarks.py` 将这些结果与 `StatisticsService` 输出逐字段比较，避免服务实现与测试共享同一查询逻辑而产生假通过。

固定数据集总览基准：

| 指标 | 期望值 |
| --- | ---: |
| 活跃社团 | 45 |
| 已完成活动 | 313 |
| 有效报名 | 19979 |
| 参与人次 | 16028 |
| 活跃学生 | 2984 |
| 到场率 | 80.22% |

## Phase 4 验收记录

- 后端：58 项测试通过，Ruff 全部通过。
- 前端：2 项测试通过，TypeScript 检查与 Vite 生产构建通过。
- 统计专项：总览、趋势、排行、分布、实体摘要和 API 参数校验均通过。
- 已知非阻塞提示：Vite 主包超过 500 kB，待前端功能稳定后通过路由懒加载拆包。

## Phase 5 验收记录

- 后端：73 项测试通过，Ruff 全部通过。
- 前端：2 项回归测试通过，TypeScript 检查与 Vite 生产构建通过。
- 真实 CRUD 闭环覆盖学生、社团、成员、活动、报名和签到，临时记录测试后清理。
- RBAC 覆盖 admin、club_manager、student，个人统计摘要仅管理员或本人可见。
- 开发库已幂等创建初始管理员和两个演示角色账号。
## Phase 6 验收记录

- 前端：4 项自动化测试通过，TypeScript 检查与 Vite 生产构建通过。
- 后端：73 项测试通过，Ruff 全部通过。
- 本机联调：登录页、管理员登录、当前用户、报名台账和统计排行均返回 200。
- 完成学生、社团、成员、活动、报名和签到操作界面，以及 7 张 Analytics 图表。
- 使用苏州工学院官网子川桥、东南图书馆照片，来源记录见 `frontend/src/assets/campus/SOURCES.md`。
- 课程项目明确不做移动端适配；生产级限流、复杂审计不在范围内。
## Phase 7 验收记录

- 核验 Hermes Agent CN Desktop 0.7.0 内置 Runtime 0.19.0，Dashboard 实际监听 `127.0.0.1:9120`。
- 核验 Ollama 模型 `qwen3.5-4b-64k:latest`，`num_ctx` 为 65536。
- 新增 Hermes CLI Adapter 及 8 项专项测试，覆盖认证、参数限制、成功、超时、缺失、失败与空响应。
- 真实链路 FastAPI → Hermes → Ollama → Qwen 返回“接口连接成功”。
## Phase 8 验收记录

- 后端全量：96 项测试通过；应用、插件与 Phase 8 测试 Ruff 全部通过。
- 令牌与权限：覆盖双重凭据、过期/用途错误 Context Token、账户回查、管理员、社团负责人和学生本人范围。
- 统计一致性：overview、两类排行、月度趋势、分布、学生摘要、社团摘要及活动类别过滤均复用 `StatisticsService`；内部 Tool 与公开 Statistics API 逐值一致。
- Hermes Runtime：用户插件 `szut-club-statistics` 0.1.0 已安装并启用，新会话成功加载 `szut_club_statistics` Toolset。
- 真实插件链路：项目插件携带短期 Context Token 调用 FastAPI overview Tool，返回 `success=true`、45 个活跃社团和既有统计基准。
## Phase 9 验收记录

- 后端全量：100 项测试通过；本次应用、插件和 Phase 9 测试 Ruff 全部通过。
- 前端：既有 4 项 Vitest 回归通过，TypeScript 检查与 Vite 生产构建通过。
- 会话闭环：覆盖创建、历史加载、删除、用户隔离、委托令牌、消息持久化、Tool 摘要和受控 Chart Specification。
- Tool Trace：覆盖单 Tool、损坏记录忽略和临时文件清理；完整 Tool 数据不持久化。
- 真实链路：管理员经 `/api/agent/chat` 调用 Hermes/Qwen 与 `get_overview_statistics`，结果为 45 个活跃社团、16028 参与人次，与 `StatisticsService` 直接查询一致。
- 已知非阻塞提示：Starlette TestClient 产生弃用提示，Vite 主包仍超过 500 kB，均安排在后续加固阶段处理。
