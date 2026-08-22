# 社团管理展示页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 快速完成内容完整、数据真实的社团管理展示页，自动化测试与深度验收后置。

**Architecture:** FastAPI 通过独立 `ClubService` 提供分页列表和详情聚合；Vue 页面通过列表、筛选和右侧详情抽屉展示社团基本信息、成员结构、活动与参与数据。所有统计来自本地 MySQL。

**Tech Stack:** FastAPI、SQLAlchemy 2 Core、MySQL 8、Vue 3、TypeScript、Axios。

## Global Constraints

- 保留完整展示内容，不实现新增、编辑、删除、认证和 RBAC。
- 暂缓专项自动化测试、边界覆盖和视觉精调，但必须完成类型检查、生产构建和在线接口检查。
- 页面视觉延续现有湖蓝、青绿、暖橙和冷灰校园数据工作台。

---

### Task 1: 社团列表与详情 API

**Files:**
- Create: `backend/app/services/clubs.py`
- Create: `backend/app/api/clubs.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /api/clubs`，支持 `search`、`category_id`、`campus_id`、`status`、`page`、`page_size`。
- Produces: `GET /api/clubs/{club_id}`，返回成员结构、活动汇总、近期活动和热门成员。

- [ ] **Step 1: 实现参数化列表查询与分页**
- [ ] **Step 2: 实现社团详情聚合查询**
- [ ] **Step 3: 注册 `/api/clubs` 路由并运行 Ruff**

### Task 2: 社团管理前端

**Files:**
- Create: `frontend/src/types/club.ts`
- Create: `frontend/src/views/ClubManagementView.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/views/StudentManagementView.vue`

**Interfaces:**
- Consumes: `GET /api/clubs` 与 `GET /api/clubs/{club_id}`。
- Produces: `/clubs` 页面及所有现有侧栏的社团管理入口。

- [ ] **Step 1: 实现摘要、搜索筛选、分页表格**
- [ ] **Step 2: 实现社团详情抽屉、成员结构与近期活动**
- [ ] **Step 3: 注册路由并连接侧栏**
- [ ] **Step 4: 运行 TypeScript 检查与生产构建**

### Task 3: 在线展示检查

**Files:**
- Modify: `docs/superpowers/plans/2026-08-22-club-management-display.md`

**Interfaces:**
- Produces: 可由用户在浏览器验收的 `/clubs` 页面。

- [ ] **Step 1: 验证列表总数为 45 且详情接口返回聚合数据**
- [ ] **Step 2: 重启演示服务并验证 `/clubs` 为 HTTP 200**
- [ ] **Step 3: 提交社团页面独立里程碑并停止等待用户验收**
