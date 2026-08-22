# Phase 6 Vue 管理与统计前端实施计划

**目标：** 将已获认可的展示版升级为桌面端可登录、可按角色操作完整业务数据的课程项目系统。

**设计方向：** 保留现有墨绿、暖金、书院气质和紧凑数据界面。抽取统一应用布局，页面继续使用清晰的内容层级、克制图表和少量校园照片，不使用炫技动效，也不做移动端适配。

**技术栈：** Vue 3、TypeScript、Pinia、Vue Router、Axios、Element Plus、ECharts、Vitest。

### Task 1：登录、会话与角色布局

**文件：**
- 新建 `frontend/src/stores/auth.ts`
- 新建 `frontend/src/types/auth.ts`
- 新建 `frontend/src/views/LoginView.vue`
- 新建 `frontend/src/layouts/AppLayout.vue`
- 修改 `frontend/src/api/http.ts`
- 修改 `frontend/src/router/index.ts`
- 修改 `frontend/src/App.vue`

- [ ] 实现登录、`/auth/me`、注销和 localStorage 会话恢复。
- [ ] Axios 自动附加 Bearer Token，401 时清理会话并返回登录页。
- [ ] 实现登录路由、权限 meta 和角色导航。
- [ ] 抽取统一侧栏、顶栏和用户菜单，迁移现有页面重复布局。

### Task 2：学生管理操作

**文件：**
- 修改 `frontend/src/views/StudentManagementView.vue`
- 新建 `frontend/src/components/students/StudentFormDialog.vue`
- 扩展 `frontend/src/types/student.ts`

- [ ] 保留现有统计、筛选、分页和详情抽屉。
- [ ] admin 增加学生、新增/编辑表单和停用确认。
- [ ] 接入学院、专业字典选项并显示接口错误。

### Task 3：社团与成员管理操作

**文件：**
- 修改 `frontend/src/views/ClubManagementView.vue`
- 新建社团表单和成员管理组件

- [ ] admin 实现社团新增、编辑、停用。
- [ ] admin/绑定 club_manager 实现成员列表、角色和状态维护。
- [ ] 非授权角色隐藏操作并由后端继续兜底。

### Task 4：活动、报名与签到管理

**文件：**
- 修改 `frontend/src/views/ActivityManagementView.vue`
- 新建活动表单、报名和签到视图/组件
- 修改 `frontend/src/router/index.ts`

- [ ] admin/club_manager 实现活动新增、编辑、状态和取消操作。
- [ ] 实现报名列表、学生本人报名/取消和管理端状态维护。
- [ ] 实现签到列表、到场/迟到/缺席修正。

### Task 5：Analytics、校园视觉与验收

**文件：**
- 新建 `frontend/src/views/AnalyticsView.vue`
- 修改 `frontend/src/views/DashboardView.vue`
- 增加来源明确的苏州工学院校园照片资源与说明
- 扩展前端测试
- 修改 `docs/ROADMAP.md`、`docs/TESTING.md`

- [ ] Dashboard 保持 4 个指标卡并补齐 6 张 ECharts 图表。
- [ ] Analytics 支持学期、校区、学院、社团和时间筛选。
- [ ] 在登录或 Dashboard 适量使用真实校园照片，保留来源记录。
- [ ] 覆盖认证 Store、路由权限、API 错误和关键表单测试。
- [ ] 运行前后端全量回归、更新文档并提交 Phase 6 里程碑。
