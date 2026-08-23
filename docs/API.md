# FastAPI 接口说明

服务默认地址为 `http://127.0.0.1:8000`，业务接口统一使用 `/api` 前缀。交互式文档位于 `/docs`。

## 认证

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/auth/login` | 用户名、密码登录并返回 Bearer JWT |
| GET | `/api/auth/me` | 返回当前用户和角色 |
| POST | `/api/auth/logout` | 注销并立即撤销当前 JWT |

开发库提供三个幂等创建的演示账号：`.env` 中配置的初始管理员、`club_manager_demo`、`student_demo`。两个演示账号的密码来自 `SEED_USER_PASSWORD`，不会写入代码或文档。

请求示例：

```http
Authorization: Bearer <access_token>
```

## 权限

| 角色 | 数据范围 |
| --- | --- |
| `admin` | 全部字典、学生、社团、活动、报名、签到和统计 |
| `club_manager` | 绑定社团的成员、活动、报名和签到 |
| `student` | 公开信息以及本人的报名和签到 |

## 业务接口

### 基础字典

资源名包括 `campuses`、`terms`、`colleges`、`majors`、`club-categories`、`activity-categories` 和 `venues`。

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| GET | `/api/dictionaries/{resource}` | 公开读取 |
| POST | `/api/dictionaries/{resource}` | admin |
| PUT | `/api/dictionaries/{resource}/{id}` | admin |
| DELETE | `/api/dictionaries/{resource}/{id}` | admin，采用停用策略 |

### 学生、社团和活动

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| GET | `/api/students`、`/api/students/{id}` | 当前展示版公开读取 |
| POST/PUT/DELETE | `/api/students...` | admin；DELETE 将状态改为 suspended |
| GET | `/api/clubs`、`/api/clubs/{id}` | 当前展示版公开读取 |
| POST/DELETE | `/api/clubs...` | admin；DELETE 将状态改为 inactive |
| PUT | `/api/clubs/{id}` | admin 或绑定的 club_manager |
| GET/PUT | `/api/clubs/{id}/members` | admin 或绑定的 club_manager |
| GET | `/api/activities`、`/api/activities/{id}` | 当前展示版公开读取 |
| POST/PUT/DELETE | `/api/activities...` | admin 或绑定的 club_manager |

有报名或签到的活动执行 DELETE 时改为 `cancelled`，无关联记录才物理删除。

### 报名与签到

| 方法 | 路径 | 权限 |
| --- | --- | --- |
| GET/POST | `/api/registrations` | admin、绑定社团经理、学生本人 |
| PATCH | `/api/registrations/{id}` | admin、绑定社团经理；学生只能取消本人报名 |
| GET | `/api/attendance` | admin、绑定社团经理、学生本人 |
| PUT | `/api/attendance` | admin 或绑定社团经理 |

### 统计

- `/api/statistics/dashboard`
- `/api/statistics/overview`
- `/api/statistics/trends/monthly`
- `/api/statistics/rankings/{club|activity|student|college}`
- `/api/statistics/distributions/{category|college|campus}`
- `/api/statistics/students/{id}`
- `/api/statistics/clubs/{id}`

统计接口支持 `term_id`、`campus_id`、`college_id`、`club_id`、`category_id`、`date_from` 和 `date_to` 过滤，统一复用 `StatisticsService`。

## 响应约定

列表响应至少包含：

```json
{"items": [], "total": 0, "page": 1, "page_size": 20}
```

部分小型字典和参与记录列表不分页，只返回 `items` 与 `total`。

错误响应统一包含：

```json
{
  "code": "FORBIDDEN",
  "message": "You do not have permission for this action",
  "request_id": "..."
}
```

每个响应还会带 `X-Request-ID` 响应头。课程项目保留必要的 JWT、角色和数据范围校验，不引入生产部署所需的限流、复杂审计和多节点令牌基础设施。
## Agent Runtime

以下接口需要 Bearer JWT，用于 Phase 7 运行环境检查和基础对话验收：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/agent/runtime` | 返回 Hermes Runtime、Dashboard、Ollama 和本地模型状态 |
| POST | `/api/agent/runtime/chat` | 通过 Hermes CLI Adapter 调用本地 Qwen；请求体为 `{"message":"..."}` |

基础对话返回 `content`、`model` 和固定的 `adapter: hermes_cli`。模型和 Provider 由服务端配置，客户端不能覆盖。Runtime 缺失、启动失败、超时、模型连接失败和空回答分别返回统一错误码。
## Internal Agent Tools

这 7 个接口仅供本机 Hermes 项目插件调用，不面向浏览器。每次请求必须同时携带 `X-Agent-Internal-Key` 和 5 分钟有效的 `X-Agent-Context-Token`。后端按 Token 的用户 ID 回查账户和权限，模型参数不能覆盖身份。

| Tool | POST 路径 |
| --- | --- |
| `get_overview_statistics` | `/api/internal/agent-tools/overview` |
| `get_club_ranking` | `/api/internal/agent-tools/club-ranking` |
| `get_activity_ranking` | `/api/internal/agent-tools/activity-ranking` |
| `get_participation_trend` | `/api/internal/agent-tools/trend` |
| `get_distribution_statistics` | `/api/internal/agent-tools/distribution` |
| `get_student_summary` | `/api/internal/agent-tools/student-summary` |
| `get_club_summary` | `/api/internal/agent-tools/club-summary` |

管理员可查询全部；社团负责人查询聚合和社团摘要时必须指定其绑定社团；学生个人摘要始终强制使用当前学生本人。参数模型禁止未知字段，排行上限为 50，趋势粒度固定为月，活动排行支持 `category_id`。
## Agent Web API

以下接口需要 Bearer JWT，会话始终按当前用户隔离：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/agent/conversations` | 按更新时间返回本人会话与消息数 |
| GET | `/api/agent/conversations/{id}/messages` | 返回本人会话消息及脱敏 Tool 摘要 |
| DELETE | `/api/agent/conversations/{id}` | 删除本人会话和消息 |
| POST | `/api/agent/chat` | 创建/续接会话并调用 Hermes 数据 Agent |

Chat 请求包含 `message`、可选 `conversation_id`，以及可选的 `context.term_id`、`context.campus_id`。响应包含最终 `answer`、`model_used`、Tool 调用摘要、首次成功 Tool 的结构化 `data`，以及后端生成的 `bar`、`line` 或 `pie` 可视化规格。客户端不能提交模型名、任意 JavaScript 或身份字段。
