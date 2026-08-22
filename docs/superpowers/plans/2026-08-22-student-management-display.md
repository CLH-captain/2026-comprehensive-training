# 学生管理展示页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成可从本地 MySQL 检索、筛选、分页并查看参与详情的学生管理展示页。

**Architecture:** FastAPI 新增只读学生列表与详情 API，查询逻辑放入独立 `StudentService`。Vue 复用现有工作台布局，通过路由进入学生管理页；筛选条件由页面状态转换为 API 参数，详情使用右侧抽屉展示。

**Tech Stack:** FastAPI、SQLAlchemy 2 Core、MySQL 8、Vue 3、TypeScript、Axios。

## Global Constraints

- 所有数字与学生记录必须来自本机 `szut_club_agent`，不得使用前端硬编码业务数据。
- API 列表使用 `page`、`page_size`，返回 `items`、`total`、`page`、`page_size`。
- 页面延续湖蓝、青绿、暖橙和冷灰的现代校园数据工作台视觉。
- 本计划只实现只读展示，不实现新增、编辑、删除、认证和 RBAC。

---

### Task 1: 学生查询 Service 与 API

**Files:**
- Create: `backend/app/services/students.py`
- Create: `backend/app/api/students.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_students_api.py`

**Interfaces:**
- Consumes: `request.app.state.engine`、`students`、`colleges`、`majors`、`club_memberships`、`activity_attendance`。
- Produces: `GET /api/students` 与 `GET /api/students/{student_id}`。

- [ ] **Step 1: 编写失败的 API 测试**

```python
def test_students_list_returns_pagination(client):
    response = client.get("/api/students?page=1&page_size=20&grade_no=1")
    assert response.status_code == 200
    assert response.json()["page_size"] == 20

def test_student_detail_returns_participation_summary(client):
    response = client.get("/api/students/1")
    assert response.status_code == 200
    assert "participation_summary" in response.json()
```

- [ ] **Step 2: 运行测试确认接口尚不存在**

Run: `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_students_api.py -q`
Expected: FAIL，响应状态为 404。

- [ ] **Step 3: 实现列表、筛选、分页和详情查询**

```python
@router.get("")
def list_students(request: Request, page: int = 1, page_size: int = 20):
    with request.app.state.engine.connect() as connection:
        return StudentService(connection).list_students(page=page, page_size=page_size)

@router.get("/{student_id}")
def student_detail(student_id: int, request: Request):
    with request.app.state.engine.connect() as connection:
        return StudentService(connection).get_student(student_id)
```

- [ ] **Step 4: 运行 API 测试与 Ruff**

Run: `backend\.venv\Scripts\python.exe -m pytest backend\tests\test_students_api.py -q`
Expected: PASS。

Run: `backend\.venv\Scripts\ruff.exe check backend\app backend\tests`
Expected: `All checks passed!`

### Task 2: 学生管理 Vue 页面

**Files:**
- Create: `frontend/src/types/student.ts`
- Create: `frontend/src/views/StudentManagementView.vue`
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/router/index.ts`

**Interfaces:**
- Consumes: `GET /api/students`、`GET /api/students/{student_id}`。
- Produces: `/students` 页面以及 Dashboard 侧栏的学生管理路由链接。

- [ ] **Step 1: 定义列表、分页、筛选与详情 TypeScript 类型**

```ts
export interface StudentListResponse {
  items: StudentListItem[]
  total: number
  page: number
  page_size: number
  filters: StudentFilters
}
```

- [ ] **Step 2: 实现页面布局和 API 状态**

```ts
async function loadStudents(): Promise<void> {
  const response = await http.get<StudentListResponse>('/students', { params: query.value })
  students.value = response.data
}
```

页面包含学生总量、学院数量、活跃参与学生、社团成员四个摘要，搜索/学院/年级/状态筛选区，分页表格和右侧详情抽屉。

- [ ] **Step 3: 注册 `/students` 路由并更新侧栏链接**

```ts
{
  path: '/students',
  name: 'students',
  component: StudentManagementView,
}
```

- [ ] **Step 4: 运行类型检查、前端测试与构建**

Run: `pnpm --dir frontend type-check`
Expected: exit code 0。

Run: `pnpm --dir frontend exec vitest run`
Expected: PASS。

Run: `pnpm --dir frontend build`
Expected: build complete。

### Task 3: 本机展示验收

**Files:**
- Modify: `docs/ROADMAP.md`

**Interfaces:**
- Consumes: 后台运行的 FastAPI、Vite 和本地 MySQL。
- Produces: 可由用户在浏览器验收的学生管理页。

- [ ] **Step 1: 只读调用接口验证真实数据**

Run: `Invoke-RestMethod http://127.0.0.1:8000/api/students?page=1&page_size=20`
Expected: `total = 3000` 且 `items.Count = 20`。

- [ ] **Step 2: 验证页面路由**

Run: `Invoke-WebRequest http://127.0.0.1:5173/students`
Expected: HTTP 200。

- [ ] **Step 3: 提交独立页面里程碑并停止等待用户验收**

```powershell
git add backend frontend docs
git commit -m "feat: add student management display"
```
