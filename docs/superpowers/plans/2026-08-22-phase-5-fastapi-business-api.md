# Phase 5 FastAPI 业务接口实施计划

**目标：** 在保持现有展示页面兼容的前提下，完成可投入前端使用的认证、权限、业务 CRUD、统一错误和 API 测试。

**架构：** API 层只负责 HTTP 校验和依赖注入；认证与权限集中在 `core/security.py`、`api/dependencies.py`；写业务按实体拆入 Service，并使用 SQLAlchemy Session 事务。`AccessScope` 在查询发生前生成社团/学生限制，禁止返回数据后再过滤。

**技术栈：** FastAPI、SQLAlchemy 2、MySQL 8、PyJWT、pwdlib Argon2、Pydantic、pytest。

## 全局约束

- 公开接口仅限健康检查、登录以及已发布活动的必要查询；管理和个人数据必须认证。
- `admin` 访问全部；`club_manager` 仅访问 `user_club_roles` 绑定社团；`student` 仅访问本人相关记录。
- JWT 必须包含 `sub`、`role`、`jti`、`iat`、`exp`，注销后的 `jti` 拒绝继续访问。
- 写操作统一事务；唯一键冲突、外键冲突和状态冲突返回稳定业务错误。
- 历史友好删除：学生停用、社团停用；有关联记录的活动取消；已引用字典返回 409。
- 错误统一返回 `code`、`message`、`request_id`，响应头带 `X-Request-ID`。

### Task 1：认证、安全基建与初始用户

**文件：**
- 新建 `backend/app/core/security.py`
- 新建 `backend/app/core/errors.py`
- 新建 `backend/app/api/dependencies.py`
- 新建 `backend/app/services/auth.py`
- 新建 `backend/app/api/auth.py`
- 修改 `backend/app/main.py`
- 测试 `backend/tests/api/test_auth.py`

- [ ] 实现 Argon2 哈希校验、JWT 创建/解析和严格 claim 校验。
- [ ] 实现 `/api/auth/login`、`/me`、`/logout` 与撤销令牌查询。
- [ ] 实现幂等初始管理员创建命令，密码只从环境变量读取。
- [ ] 实现 request_id 中间件和统一异常响应。
- [ ] 覆盖成功登录、错误密码、禁用账号、过期/伪造/撤销令牌测试。

### Task 2：RBAC 与查询作用域

**文件：**
- 新建 `backend/app/core/permissions.py`
- 扩展 `backend/app/api/dependencies.py`
- 测试 `backend/tests/api/test_rbac.py`

- [ ] 定义 `CurrentUser`、`AccessScope` 和角色依赖。
- [ ] 从 `user_club_roles` 加载社团经理的允许社团集合。
- [ ] 将社团/学生作用域传入 Service 查询条件，在数据库层限制结果。
- [ ] 覆盖 admin、club_manager、student 的允许与拒绝矩阵。

### Task 3：基础字典、学生和社团 CRUD

**文件：**
- 新建 `backend/app/schemas/common.py`
- 新建/扩展字典、学生、社团 Schema、Service 和 API 模块
- 测试 `backend/tests/api/test_dictionaries.py`
- 测试 `backend/tests/api/test_students_crud.py`
- 测试 `backend/tests/api/test_clubs_crud.py`

- [ ] 实现 campuses、terms、colleges、majors、club/activity categories、venues 查询与管理员维护。
- [ ] 实现学生创建、更新、详情、列表和停用。
- [ ] 实现社团创建、更新、详情、列表、停用及成员关系维护。
- [ ] 保持现有列表响应和展示字段兼容，并增加权限作用域。

### Task 4：活动、报名和签到 CRUD

**文件：**
- 新建/扩展活动、报名、签到 Schema、Service 和 API 模块
- 测试 `backend/tests/api/test_activities_crud.py`
- 测试 `backend/tests/api/test_registrations.py`
- 测试 `backend/tests/api/test_attendance.py`

- [ ] 实现活动创建、更新、发布、完成、取消和历史友好删除。
- [ ] 实现报名创建/取消/候补及容量、重复报名、时间状态校验。
- [ ] 实现签到创建/修正，保证学生、活动和报名关系一致。
- [ ] 实现按活动、社团和本人范围查询报名与签到。

### Task 5：Statistics 权限接入、文档与阶段验收

**文件：**
- 修改 `backend/app/api/statistics.py`
- 新建 `docs/API.md`
- 修改 `docs/TESTING.md`
- 修改 `docs/ROADMAP.md`

- [ ] 将 Statistics 筛选器与 `AccessScope` 合并，防止越权传参。
- [ ] 完成参数校验、分页元数据、错误码和 request_id 的兼容测试。
- [ ] 运行后端全量 pytest/Ruff 与前端回归测试/构建。
- [ ] 编写 API 文档、更新路线图并提交 Phase 5 里程碑。
