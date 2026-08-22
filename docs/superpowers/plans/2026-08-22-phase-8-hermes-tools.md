# Phase 8 Hermes Plugin 与 Internal Tool API 实施计划

**目标：** 为 Hermes 提供 7 个严格、可授权、可测试的统计工具；所有数字继续由现有 `StatisticsService` 从 MySQL 计算，不新增第二套统计 SQL。

**权限方向：** FastAPI 生成短期 Agent Context Token。内部接口同时验证 `X-Agent-Internal-Key` 与 Context Token，并按 Token 中的用户 ID回查数据库重建权限；管理员可查全部，社团负责人仅限绑定社团，学生个人摘要强制限定本人。

### Task 1：Agent 委托令牌与内部认证

- [ ] 实现 5 分钟 Agent Context Token 的创建、解析和用途声明。
- [ ] 使用常量时间比较验证 `X-Agent-Internal-Key`。
- [ ] 从数据库回查用户状态、角色、学生身份和社团绑定，禁止信任模型参数中的身份。

### Task 2：7 个 Internal Tool API

- [ ] 实现 overview、club-ranking、activity-ranking、trend、distribution。
- [ ] 实现 student-summary、club-summary。
- [ ] 所有请求模型 `extra=forbid`，限制枚举、日期范围、ID 和 limit。
- [ ] 全部调用 `StatisticsService`，不在 Tool 路由编写统计 SQL。

### Task 3：项目级 Hermes Plugin

- [ ] 建立 `hermes_plugin/szut-club-statistics` 项目插件。
- [ ] 注册 7 个严格 Tool Schema 和最小 HTTP Client。
- [ ] Key、Context Token 与 FastAPI 地址只从环境变量读取。

### Task 4：权限测试与文档

- [ ] 覆盖双重认证、过期/用途错误 Token、管理员、负责人和学生数据范围。
- [ ] 对 Tool 结果与 `StatisticsService` 建立一致性断言。
- [ ] 更新 API、测试说明和路线图，运行后端全量回归。
