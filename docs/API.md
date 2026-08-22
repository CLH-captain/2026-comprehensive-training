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

统计接口支持 `term_id`、`campus_id`、`college_id`、`club_id`、`date_from` 和 `date_to` 过滤，统一复用 `StatisticsService`。

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
