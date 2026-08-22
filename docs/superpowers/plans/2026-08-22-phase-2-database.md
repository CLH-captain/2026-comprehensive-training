# Phase 2 Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 SQLAlchemy 2 和 Alembic 实现开发基线中的全部业务、认证和 Agent 数据表，并在独立 MySQL 测试库验证约束、索引与迁移。

**Architecture:** `app.models` 按校园基础数据、学生、社团、活动、认证、Agent 六个领域拆分；`app.db` 只负责 Base、命名约定、Engine 和 Session。模型使用 SQLAlchemy 2 `Mapped` 声明；所有结构变化只由 Alembic 迁移应用。

**Tech Stack:** SQLAlchemy 2.0、PyMySQL、Alembic、MySQL 8.0、pytest。

## Global Constraints

- 开发库固定为 `szut_club_agent`，测试库固定为 `szut_club_agent_test`。
- 测试和 reset 代码必须拒绝任何不以 `_test` 结尾的数据库 URL。
- 所有表使用 InnoDB、utf8mb4；迁移不可依赖 SQLite 专有行为。
- 主键使用 BIGINT 自增；外键、唯一约束和高频筛选列必须显式命名。
- 业务历史表禁止级联物理删除；仅会话消息使用受控级联。

---

### Task 1: Database Infrastructure and Safety Guard

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/tests/test_database_safety.py`

**Interfaces:**
- Produces: `Base`, `create_engine_from_url(url)`, `create_session_factory(engine)`, `assert_test_database_url(url)`。

- [ ] 先测试 `assert_test_database_url()` 接受 `szut_club_agent_test`，拒绝 `szut_club_agent`、空 URL 和其他库名。
- [ ] 为 MetaData 定义 `ix/uq/ck/fk/pk` 命名约定，保证 Alembic 输出稳定。
- [ ] Engine 启用 `pool_pre_ping=True`、`pool_recycle=1800`，Session 使用 `autoflush=False`、`expire_on_commit=False`。
- [ ] 运行 `pytest backend/tests/test_database_safety.py -q` 和 Ruff。
- [ ] 提交 `feat: add database infrastructure safeguards`。

### Task 2: Campus Reference Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/enums.py`
- Create: `backend/app/models/mixins.py`
- Create: `backend/app/models/campus.py`
- Create: `backend/tests/test_model_metadata.py`

**Interfaces:**
- Produces: `Campus`, `AcademicTerm`, `College`, `Major`, `Venue` 及共享时间戳/枚举。

- [ ] 用 metadata 测试断言表名、BIGINT 主键、唯一编码、外键和 `academic_year + term_no` 唯一约束。
- [ ] 实现 campuses、academic_terms、colleges、majors、venues；布尔默认值在 Python 与 server_default 同时定义。
- [ ] Venue 的 `capacity > 0`，AcademicTerm 的 `term_no IN (1,2)`、`start_date < end_date` 使用 CheckConstraint。
- [ ] 运行 metadata 测试与 Ruff。
- [ ] 提交 `feat: add campus reference models`。

### Task 3: Student and Club Models

**Files:**
- Create: `backend/app/models/student.py`
- Create: `backend/app/models/club.py`
- Extend: `backend/tests/test_model_metadata.py`

**Interfaces:**
- Produces: `Student`, `ClubCategory`, `Club`, `ClubMembership`。

- [ ] 测试学生学号唯一、专业归属外键、社团编码唯一、成员 `(club_id, student_id)` 唯一。
- [ ] 用枚举约束 Student status、Club status、Membership role/status。
- [ ] 对 college/major/year/grade/status、club category/campus/status 和 membership student/status 建索引。
- [ ] 运行测试和 Ruff；提交 `feat: add student and club models`。

### Task 4: Activity Participation Models

**Files:**
- Create: `backend/app/models/activity.py`
- Extend: `backend/tests/test_model_metadata.py`

**Interfaces:**
- Produces: `ActivityCategory`, `Activity`, `ActivityRegistration`, `ActivityAttendance`。

- [ ] 测试活动编码唯一、时间约束、容量约束、报名和签到各自 `(activity_id, student_id)` 唯一。
- [ ] 实现活动、报名、签到枚举和可空 registration 外键。
- [ ] 为统计热点建立 `(term_id,status,start_time)`、`(club_id,status)`、`(activity_id,status)`、`(student_id,status)` 组合索引。
- [ ] 运行测试和 Ruff；提交 `feat: add activity participation models`。

### Task 5: Authentication and Agent Persistence Models

**Files:**
- Create: `backend/app/models/auth.py`
- Create: `backend/app/models/agent.py`
- Extend: `backend/tests/test_model_metadata.py`

**Interfaces:**
- Produces: `User`, `UserClubRole`, `RevokedToken`, `AgentConversation`, `AgentMessage`。

- [ ] 测试用户名唯一、用户社团角色唯一、JWT jti 唯一、消息与会话级联关系。
- [ ] 密码字段只命名 `password_hash`；消息保存 JSON Tool 摘要但不提供隐藏推理字段。
- [ ] 为用户角色/状态、Token 过期时间、会话用户/更新时间、消息会话/创建时间建索引。
- [ ] 运行测试和 Ruff；提交 `feat: add auth and agent persistence models`。

### Task 6: Alembic Baseline and MySQL Verification

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/<revision>_create_initial_schema.py`
- Create: `backend/tests/test_migrations.py`
- Create: `backend/scripts/create_databases.sql`

**Interfaces:**
- Consumes: 全部 Model metadata、`DATABASE_URL`、`TEST_DATABASE_URL`。
- Produces: 可从空库升级到完整结构并降级为空库的 Alembic 基线。

- [ ] 配置 Alembic 从 Settings 读取 URL，导入所有模型 metadata，不在 ini 中写密码。
- [ ] 自动生成后人工审查首个迁移；确认 18 张表、约束、索引、外键和降级顺序完整。
- [ ] 迁移测试先调用 `assert_test_database_url()`，对测试库执行 downgrade base → upgrade head → metadata 反射断言。
- [ ] 在开发库执行 `alembic upgrade head`，不执行 destructive reset。
- [ ] 运行全部后端测试、Ruff 和 `alembic check`。
- [ ] 更新 `docs/DATABASE.md` 与 ROADMAP；提交 `feat: establish initial MySQL schema`。

## Phase 2 Completion Gate

- 18 张表均由 Alembic 创建，开发库和测试库可升级。
- 测试库可安全降级再升级；开发库不参与 destructive 测试。
- 模型 metadata、约束、索引、外键和迁移测试通过。
- 后端既有健康检查测试不回归。
