# Phase 4 Statistics Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 建立 Dashboard、Statistics API 和后续 Agent Tool 共用的确定性统计层，并用固定种子数据验证所有核心数字。

**Architecture:** 新建 `app/statistics` 包，将筛选条件、总览、趋势、排行、分布和实体摘要拆为独立查询模块，`StatisticsService` 作为唯一门面。现有 Dashboard API 改为调用门面；统计测试只读访问隔离测试库，并用独立基准 SQL 对比结果。

**Tech Stack:** Python 3.11、SQLAlchemy 2 Core、MySQL 8、FastAPI、pytest。

## Global Constraints

- 已开展活动仅统计 `activities.status = completed`。
- 参与人次与活跃学生仅统计签到 `present`、`late`。
- 有效报名仅统计 `registered`；到场率分母为零时返回 `null`。
- 活动校区按场地校区，趋势区间左闭右开，缺失月份补零，比率保留两位。
- 排名同值按名称、ID 稳定排序，默认 10，最大 100。
- 社团活跃度为活动数 50%、参与人次 30%、独立学生 20% 的最大值归一化加权。

---

### Task 1: 统计筛选与公共查询边界

**Files:**
- Create: `backend/app/statistics/__init__.py`
- Create: `backend/app/statistics/filters.py`
- Create: `backend/app/statistics/common.py`
- Test: `backend/tests/statistics/test_filters.py`

**Interfaces:**
- Produces: `StatisticsFilter(term_id, campus_id, college_id, club_id, date_from, date_to)`。
- Produces: `activity_where(alias="a", venue_alias="v") -> tuple[str, dict]`，所有模块共享同一筛选语义。

- [x] **Step 1: 编写筛选参数与日期左闭右开测试**

```python
filters = StatisticsFilter(term_id=2, campus_id=1, date_from=date(2026, 3, 1), date_to=date(2026, 4, 1))
where, params = filters.activity_where()
assert "a.term_id = :term_id" in where
assert params["date_to"] == datetime(2026, 4, 1)
```

- [x] **Step 2: 实现冻结 dataclass、参数化 WHERE 和月份序列补零工具**
- [x] **Step 3: 运行 `pytest backend/tests/statistics/test_filters.py -q` 和 Ruff**

### Task 2: 总览、趋势与分布

**Files:**
- Create: `backend/app/statistics/overview.py`
- Create: `backend/app/statistics/trends.py`
- Create: `backend/app/statistics/distributions.py`
- Test: `backend/tests/statistics/test_overview.py`

**Interfaces:**
- Produces: `overview(connection, filters) -> dict`。
- Produces: `monthly_trend(connection, filters) -> list[dict]`，自动补齐月份。
- Produces: `category_distribution`、`college_distribution`、`campus_distribution`。

- [x] **Step 1: 编写固定数据集总览与月份补零测试**
- [x] **Step 2: 实现总览、月度趋势、类别/学院/校区分布查询**
- [x] **Step 3: 运行专项测试并确认比率为两位小数或 `None`**

### Task 3: 排行、实体摘要与统一活跃度

**Files:**
- Create: `backend/app/statistics/rankings.py`
- Create: `backend/app/statistics/summaries.py`
- Test: `backend/tests/statistics/test_rankings.py`
- Test: `backend/tests/statistics/test_summaries.py`

**Interfaces:**
- Produces: `club_ranking`、`activity_ranking`、`student_ranking`、`college_ranking`。
- Produces: `student_summary(student_id)` 与 `club_summary(club_id)`。
- Produces: 每个社团 `activity_score`，范围 `0.00..100.00`。

- [x] **Step 1: 编写稳定排序、limit 上限和活跃度公式测试**
- [x] **Step 2: 实现四类排行及社团活跃度**
- [x] **Step 3: 实现学生/社团摘要及不存在实体处理**
- [x] **Step 4: 运行排行和摘要专项测试**

### Task 4: StatisticsService 门面与 API

**Files:**
- Create: `backend/app/statistics/service.py`
- Modify: `backend/app/services/statistics.py`
- Modify: `backend/app/api/statistics.py`
- Modify: `frontend/src/types/dashboard.ts`
- Test: `backend/tests/statistics/test_api.py`

**Interfaces:**
- Produces: `StatisticsService.dashboard(filters)`，兼容现有 Dashboard 响应。
- Produces: `/api/statistics/overview`、`/trends/monthly`、`/rankings/{dimension}`、`/distributions/{dimension}`、`/students/{id}`、`/clubs/{id}`。

- [x] **Step 1: 实现门面并让现有 Dashboard 复用新模块**
- [x] **Step 2: 实现严格枚举、limit 和筛选参数 API**
- [x] **Step 3: 编写 API 成功、参数错误和不存在实体测试**
- [x] **Step 4: 运行 Dashboard 前端类型检查与后端 API 测试**

### Task 5: 独立 SQL 基准与阶段验收

**Files:**
- Create: `backend/tests/statistics/benchmark_queries.py`
- Create: `backend/tests/statistics/test_benchmarks.py`
- Modify: `docs/ROADMAP.md`
- Modify: `docs/TESTING.md`

**Interfaces:**
- Consumes: `TEST_DATABASE_URL`，并先调用 `assert_test_database_url`。
- Produces: 固定种子数据下服务结果与独立 SQL 结果 100% 一致的验收记录。

- [x] **Step 1: 为总览、趋势、四类排行和三类分布编写独立基准 SQL**
- [x] **Step 2: 对比 Service DTO 与基准结果，失败时报告具体维度**
- [x] **Step 3: 运行后端全量 pytest、Ruff、前端测试/类型检查/构建**
- [x] **Step 4: 更新 Phase 4 路线图与测试文档并提交阶段里程碑**
