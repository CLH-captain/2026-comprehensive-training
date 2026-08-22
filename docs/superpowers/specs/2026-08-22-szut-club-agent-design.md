# 苏州工学院校园社团活动参与统计 Agent 系统设计

## 1. 目标与范围

本项目按照《苏州工学院校园社团活动参与统计 Agent》V2.0 开发基线，构建可真实运行的数据闭环：Vue 3 前端通过 FastAPI 管理和分析 MySQL 中的校园社团活动仿真数据，并通过独立 Hermes Agent 使用预定义 Tool 完成自然语言统计查询。

当前主线覆盖原文档 Phase 1～11。实训报告和答辩 PPT 在系统验收后单独制作；MCP、Skills、Excel、自动报告、Text-to-SQL、多 Agent 等 Phase 12 扩展不纳入当前 MVP。

项目代码位于 `D:\文档\实训2026\社团活动参与统计Agent\szut-club-agent`。

## 2. 已确认的运行环境

- Windows 本机开发与答辩演示；不使用 Docker。
- Python 3.11，项目使用独立 `.venv`；Node.js 24、pnpm 11。
- 本机 MySQL 8.0.43，监听 `127.0.0.1:3306`。
- 开发数据库 `szut_club_agent`；隔离测试数据库 `szut_club_agent_test`。
- Hermes Agent CN Desktop 0.7.0：`D:\Hermes\Hermes Agent CN Desktop`。
- Ollama 0.30.4：`D:\ollama-windows-amd64\ollama.exe`。
- Ollama 模型目录：`D:\ollama-windows-amd64\models`。
- 主模型：`qwen3.5-4b-64k:latest`。
- 自定义模型文件：`D:\ollama_custom\Modelfile`，配置 `num_ctx 65536`、`temperature 0.3`。
- DeepSeek API 已具备，地址和 Key 后续仅写入本地 `.env`。

## 3. 总体架构

采用模块化单体。Vue 和 FastAPI 分别运行，Hermes 独立运行；后端使用同步 SQLAlchemy 2 + PyMySQL，以降低 Windows 环境与测试复杂度。

```text
Vue 3 :5173
    │ JWT / REST
    ▼
FastAPI :8000
    ├── API：HTTP、校验、鉴权、响应
    ├── Service：业务规则
    ├── Statistics：统一统计口径
    ├── Repository：SQLAlchemy 查询
    ├── Agent Adapter：调用 Hermes
    └── Internal Tool API：供 Hermes 插件调用
             │
             ├──────── MySQL 8 :3306
             ▼
Hermes Agent CN Desktop 0.7.0 :8642（端口配置化）
    ├── Primary：Ollama / qwen3.5-4b-64k:latest
    ├── Fallback：DeepSeek-v4-flash
    └── SZUT Plugin：调用 Internal Tool API
```

FastAPI 是前端唯一后端入口。前端不得直连 MySQL、Hermes 或 Ollama。Hermes 不得直连数据库，只能通过 Internal Tool API 调用现有 Service/Statistics。Hermes 0.7.0 的实际 API 和插件接口在 Phase 7 核验；若与基线示例不同，由 Adapter 适配，禁止修改 Hermes Core。

## 4. 仓库与模块边界

```text
szut-club-agent/
├── frontend/
├── backend/
├── hermes_plugin/szut-club-statistics/
├── data/{generated,samples}/
├── docs/{PROJECT_SPEC.md,DATABASE.md,API.md,TESTING.md}
├── scripts/
├── .env.example
├── .gitignore
├── README.md
└── AGENTS.md
```

后端遵循 `API → Service/Statistics → Repository → Model → MySQL`。文件按业务能力拆分，避免巨型路由、Service 或 Model 文件。前端按 API、组件、布局、路由、Store、类型和业务视图拆分。

## 5. 数据模型与生命周期

实现基线定义的 campuses、academic_terms、colleges、majors、students、club_categories、clubs、club_memberships、activity_categories、venues、activities、activity_registrations、activity_attendance、users、user_club_roles、agent_conversations、agent_messages，并增加 `revoked_tokens` 支持 JWT 注销。

所有结构变更使用 Alembic。外键列和高频筛选列建立索引；报名、签到和社团成员保留联合唯一约束。重点组合索引覆盖学期、校区、活动时间、状态、社团和学生维度。

删除采用历史友好策略：学生转为非活跃；社团转为 `inactive`；有报名或签到的活动转为 `cancelled`，无关联记录才物理删除；报名和签到通过状态更新纠正；已被引用的基础字典拒绝删除并返回 `409 Conflict`。

## 6. 仿真数据生成

生成器使用固定随机种子 `20260822`，实现学院权重、年级参与差异、社团长尾、学院活动兴趣、月份峰谷、活动规模、报名概率、到场率和合理异常。

生成流程先构造一致的数据图并验证，再在事务中写入 MySQL，同时导出 CSV 和 `data_quality_report.json`。失败时回滚，不产生半套数据。`--reset` 只操作显式选择的项目数据库；测试固定使用 `szut_club_agent_test`，不清理开发库。

质量检查覆盖数量、外键、唯一性、时间、容量、报名/到场率、年级分布、社团长尾、活动规模和月份趋势。

## 7. 统一统计口径

Dashboard、Statistics API 和 Agent Tool 共享同一 `StatisticsService`：

- 学期按 `activities.term_id`。
- 活动校区按 `venues.campus_id`；社团所属校区按 `clubs.home_campus_id`。
- “某校区活动/参与”按活动实际举办场地统计。
- 已开展活动仅统计 `activities.status = completed`。
- 参与人次与活跃学生仅统计签到 `present`、`late`。
- 有效报名仅统计 `registered`。
- 到场率为实际到场人数除以有效报名人数；分母为零返回 `null`。
- 时间按 `Asia/Shanghai` 解释，区间左闭右开，趋势缺失周期补零。
- 排名同值时按名称、ID 稳定排序；默认 limit 10，最大 100。
- 比率输出四舍五入到两位小数。

社团活跃度使用最大值归一化：

```text
活动数量分数 = 当前活动数量 / 筛选集最大活动数量 × 100
参与人次分数 = 当前参与人次 / 筛选集最大参与人次 × 100
独立学生分数 = 当前独立学生数 / 筛选集最大独立学生数 × 100
活跃度 = 0.5 × 活动数量分数 + 0.3 × 参与人次分数 + 0.2 × 独立学生分数
```

某项最大值为零时该项分数为零。统计层返回结构化 DTO，Chart Specification 由确定性转换器生成。

## 8. API、认证与权限

API 使用 `/api` 前缀。列表接口使用 `page`、`page_size`，返回 `items`、`total`、`page`、`page_size`。错误统一返回 `code`、`message`、`request_id`。

密码使用 Argon2。JWT Access Token 含唯一 `jti`；注销时写入 `revoked_tokens`。初始管理员由 `INITIAL_ADMIN_USERNAME`、`INITIAL_ADMIN_PASSWORD` 创建；仿真演示账号初始密码来自 `SEED_USER_PASSWORD`，均不得硬编码或提交。

- admin 可访问全部数据。
- club_manager 只访问绑定社团及其成员、活动、报名、签到和统计。
- student 只访问公开资源和本人记录。
- 权限作用域进入 Service/Repository 查询条件，禁止前端过滤或查询后再过滤。

Agent 使用短期签名的 Agent Context Token。FastAPI 只写入用户 ID 和会话标识；Internal Tool API 验证该令牌和 `X-Agent-Internal-Key` 后，从数据库重新计算权限。模型不能通过参数指定其他学生绕过权限。

## 9. Agent 与 Fallback

FastAPI 使用独立 `HermesClient` Adapter。Hermes 地址、Key、API 路径、模型、超时和重试全部配置化。插件只包含 Tool Schema 和 HTTP Client，不含 SQL、统计公式或权限判断。

Tool 参数使用严格枚举、范围和未知字段校验。“本学期”使用后端验证后的 `term_id`。会话只保存用户消息、最终回答、模型名和脱敏 Tool 摘要，不保存隐藏推理。确定性数字必须来自 Tool 结果。

Fallback 在 Ollama 连接失败/超时、本地响应重试一次后仍无法解析、Tool Calling 连续两次格式无效或 Hermes 返回可恢复模型错误时触发。无数据、权限不足和参数错误不触发 Fallback。

DeepSeek 只接收用户问题、系统约束和脱敏聚合结果。JWT、Key、密码、数据库结构和原始个人记录不得上传。个人明细默认禁止云端 Fallback。若 Hermes 0.7.0 不支持所需编排，由 FastAPI Adapter 实现。

图表只返回受控的 bar、line、pie Chart Specification，不接受模型生成 JavaScript。

## 10. 前端设计

视觉方向为“现代校园数据工作台”：稳重、清晰、有辨识度，不使用夸张渐变、玻璃拟态、霓虹效果或大量动画，也避免传统灰白后台模板的老旧感。

- 主色为湖蓝/青绿色，暖橙用于重点和预警。
- 冷灰背景、白色卡片、细边框和克制阴影建立层级。
- 左侧导航按角色显示；顶栏固定学期、校区和用户菜单。
- 表格页采用筛选区、表格、分页和抽屉表单。
- Analytics 筛选条件同步 URL。
- Agent 页面展示上下文、快捷问题、回答、Tool 数据表格和 ECharts 图表。
- Pinia 只保存身份和跨页筛选状态。

少量真实校园照片用于登录页主视觉、Dashboard 顶部横幅和 Agent 欢迎区。素材仅选苏州工学院官网及官方新闻网可追溯图片，下载为本地静态资源，压缩并提供替代文本；文档记录原始链接和用途。不混用名称相近学校图片，不将照片作为仿真数据真实性背书。正式公开发布前由项目所有者确认素材授权。

## 11. 错误处理与日志

每个请求生成 `request_id`，贯穿响应头、错误响应和日志。数据库写操作使用事务。全局异常处理器只返回安全信息；开发环境才记录详细堆栈。

MySQL、Hermes、Ollama、DeepSeek 分别配置连接和响应超时。日志采用结构化 JSON，自动遮蔽密码、JWT、API Key、内部 Key 和 Authorization Header。Agent 日志记录会话、模型、Fallback、Tool、耗时和错误类型，不记录隐藏推理或完整个人数据。

## 12. 测试策略

- 后端 pytest：Model、Repository、Service、Statistics、RBAC、API。
- 数据测试：固定种子、数量、外键、唯一性、时间、容量和业务分布。
- 前端 Vitest + Vue Test Utils：Store、权限路由、API 错误和关键组件。
- Playwright 冒烟：登录、Dashboard、核心 CRUD、Analytics、Agent 页面。
- Agent 标准集：40 个问题，覆盖总量、条件、排名、趋势、学院、校区、活动、转化、社团、个人和综合总结。
- 确定性统计与 SQL 基准答案对比，目标 100%。
- 关闭 Ollama 后验证普通聚合查询切换 DeepSeek；个人明细拒绝云端降级。

每个 Phase 完成后运行阶段测试和已有回归测试，项目始终保持可启动。

## 13. 分阶段交付

1. 初始化仓库、前后端、环境模板、README 和本机服务检查。
2. SQLAlchemy Models、Alembic、外键、索引和数据库测试。
3. 仿真数据生成、MySQL Seed、CSV、质量报告和数据测试。
4. Statistics Service 与单元测试。
5. JWT、RBAC、CRUD、Statistics API 和 API 测试。
6. Vue 登录、布局、Dashboard、管理页和 Analytics。
7. 核验并接入 Hermes 0.7.0 与本地 Qwen。
8. 实现 Hermes Plugin 与 Internal Tool API。
9. 完成 Vue → FastAPI → Hermes → Tool → MySQL 闭环。
10. 接入 DeepSeek Fallback 并验证脱敏和禁用场景。
11. 完成图表、会话、日志、异常处理、UI 和全量回归。

每阶段产生可验证成果，不一次性生成空壳。Phase 12、实训报告和 PPT 在 MVP 验收后另行规划。

## 14. 验收标准

- 至少 3000 名学生、40 个社团、300 场活动、18000 条报名、15000 条签到/参与记录。
- Dashboard 至少 4 个指标卡和 5 张来自 MySQL 的图表。
- 学生、社团、活动正常管理；报名和签到状态可管理。
- 可按学期、校区、学院、社团和时间统计。
- Agent 完成总量、条件、排名、趋势、学院、社团和综合分析。
- Dashboard、API、Agent 对同一问题返回一致数字。
- 本地 Qwen 正常推理；停止本地模型后普通聚合查询可用 DeepSeek。
- RBAC、Agent 委托令牌、个人明细禁用云端 Fallback 均有自动化测试。
- README 可指导在当前 Windows + 本机 MySQL 环境中安装、迁移、Seed、启动和测试。

## 15. 明确不实现

当前 MVP 不实现人脸识别、GPS、二维码签到、微信小程序、手机 App、知识图谱、RAG、向量数据库、多 Agent、推荐算法、Text-to-SQL、真实学生数据爬取、自训练模型、MCP Server 或业务 Skills。
