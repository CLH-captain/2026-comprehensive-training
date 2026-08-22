# 数据库设计

## 环境与安全边界

- 数据库：MySQL 8.0，InnoDB，utf8mb4。
- 开发库：`szut_club_agent`。
- 测试库：`szut_club_agent_test`。
- `assert_test_database_url()` 会拒绝在开发库或其他库执行 destructive 测试。
- 所有结构变化通过 `backend/alembic` 管理。

## 表分组

校园基础数据：

- `campuses`
- `academic_terms`
- `colleges`
- `majors`
- `venues`

学生与社团：

- `students`
- `club_categories`
- `clubs`
- `club_memberships`

活动参与：

- `activity_categories`
- `activities`
- `activity_registrations`
- `activity_attendance`

认证与权限：

- `users`
- `user_club_roles`
- `revoked_tokens`

Agent：

- `agent_conversations`
- `agent_messages`

## 核心约束

- 同一学年和学期编号唯一。
- 同一学生在同一社团只能有一条成员记录。
- 同一学生对同一活动只能有一条报名和一条签到记录。
- 活动开始时间早于结束时间，容量必须大于零。
- 场地容量必须大于零。
- 用户社团管理角色 `(user_id, club_id)` 唯一。
- Agent 消息只保存最终内容与 Tool 摘要，不存在隐藏推理字段。

## 统计索引

高频组合索引覆盖：

- 活动学期、状态、开始时间。
- 活动社团和状态。
- 报名活动/学生和状态。
- 签到活动/学生和状态。
- 学生学院、专业和状态。
- 社团类别、校区和状态。

## 迁移命令

从项目根目录执行：

```powershell
backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

检查 metadata 与迁移是否一致：

```powershell
backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini check
```

测试库降级属于 destructive 操作，执行前必须通过测试库 URL 守卫。开发库不自动降级或重建。
