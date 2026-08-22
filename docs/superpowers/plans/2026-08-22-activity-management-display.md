# 活动管理展示页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 完成内容完整、数据真实的活动管理展示页，专项自动化测试与深度验收后置。

**Architecture:** FastAPI 的 `ActivityService` 聚合活动、报名、签到、社团、场地与学期信息，提供分页列表和详情 API。Vue 页面以筛选表格和详情抽屉呈现活动全生命周期数据。

**Tech Stack:** FastAPI、SQLAlchemy 2 Core、MySQL 8、Vue 3、TypeScript、Axios。

## Global Constraints

- 展示内容覆盖活动基础信息、业务状态、容量、报名、签到和到场率。
- 不实现新增、编辑、删除、认证和 RBAC。
- 暂缓专项自动化测试和深度视觉验收，但完成 Ruff、TypeScript、生产构建和在线接口检查。

---

### Task 1: 活动列表与详情 API

**Files:**
- Create: `backend/app/services/activities.py`
- Create: `backend/app/api/activities.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /api/activities`，支持 `search`、`term_id`、`category_id`、`club_id`、`campus_id`、`status`、分页。
- Produces: `GET /api/activities/{activity_id}`，返回报名/签到结构和参与学生预览。

- [x] **Step 1: 实现活动分页、筛选和摘要查询**
- [x] **Step 2: 实现活动详情、状态分布和参与学生查询**
- [x] **Step 3: 注册路由并运行 Ruff**

### Task 2: 活动管理 Vue 页面

**Files:**
- Create: `frontend/src/types/activity.ts`
- Create: `frontend/src/views/ActivityManagementView.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/views/StudentManagementView.vue`
- Modify: `frontend/src/views/ClubManagementView.vue`

**Interfaces:**
- Consumes: `GET /api/activities` 与 `GET /api/activities/{activity_id}`。
- Produces: `/activities` 页面及所有侧栏的活动管理入口。

- [x] **Step 1: 实现活动摘要、完整筛选、分页表格和状态标识**
- [x] **Step 2: 实现活动详情抽屉、容量进度、报名/签到结构和参与名单**
- [x] **Step 3: 注册路由并连接全部现有侧栏**
- [x] **Step 4: 运行 TypeScript 检查与生产构建**

### Task 3: 在线展示检查

**Files:**
- Modify: `docs/superpowers/plans/2026-08-22-activity-management-display.md`

**Interfaces:**
- Produces: 可由用户浏览器验收的 `/activities` 页面。

- [x] **Step 1: 检查活动总数 324、分页记录和详情聚合**
- [x] **Step 2: 重启服务并验证 `/activities` 为 HTTP 200**
- [x] **Step 3: 提交活动页面独立里程碑**
