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
