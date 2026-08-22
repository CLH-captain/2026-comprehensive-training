# 苏州工学院校园社团活动参与统计 Agent

本项目使用 Vue 3、FastAPI、MySQL 与 Hermes Agent 构建校园社团活动数据管理、统计分析和自然语言查询平台。所有业务数据均为固定种子生成的仿真数据；所有统计数字以 MySQL 为唯一来源。

当前可展示版本已完成本机 MySQL 配置、18 张业务表、固定种子仿真数据、Statistics Service 与 Vue 数据总览。Hermes、完整 CRUD 和权限功能按路线图继续开发。

## 本机环境

- Windows
- Python 3.11+
- Node.js 22+
- pnpm 11+
- MySQL 8，`127.0.0.1:3306`
- Hermes Agent CN Desktop 0.7.0
- Ollama 0.30.4
- `qwen3.5-4b-64k:latest`

先检查环境：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-environment.ps1
```

Hermes 与 Ollama 在 Phase 7 前可以不启动；检查脚本会将其端口显示为警告而不是失败。

## 准备 MySQL

使用 MySQL 管理账号登录后，只创建本项目的开发库、测试库和最小权限用户。请把示例密码换成独立强密码：

```sql
CREATE DATABASE IF NOT EXISTS szut_club_agent
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE DATABASE IF NOT EXISTS szut_club_agent_test
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'szut_user'@'127.0.0.1'
  IDENTIFIED BY 'replace-with-strong-password';
GRANT ALL PRIVILEGES ON szut_club_agent.* TO 'szut_user'@'127.0.0.1';
GRANT ALL PRIVILEGES ON szut_club_agent_test.* TO 'szut_user'@'127.0.0.1';
FLUSH PRIVILEGES;
```

项目的重置和测试脚本只允许操作这两个库，不触碰其他数据库。

## 配置环境变量

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

把第二条命令生成的不同随机值分别用于 `.env` 中的 `JWT_SECRET` 和 `AGENT_INTERNAL_KEY`，并填写：

- `DATABASE_URL`、`TEST_DATABASE_URL` 中的 MySQL 密码
- `INITIAL_ADMIN_PASSWORD`、`SEED_USER_PASSWORD`
- `HERMES_API_KEY`
- `DEEPSEEK_API_KEY`

`.env` 已被 Git 忽略。不要把真实密码或 Key 写入 `.env.example`、README、测试或提交记录。

## 快速启动初版演示

数据库已迁移并完成 Seed 后，在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start-demo.ps1
```

浏览器访问 `http://127.0.0.1:5173`，API 文档位于 `http://127.0.0.1:8000/docs`。结束演示：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop-demo.ps1
```

Dashboard 展示的数据实时来自本机 MySQL，可按学期和校区筛选。

## 启动后端

首次安装：

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
```

启动：

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

验证：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

## 启动前端

首次安装：

```powershell
pnpm install
```

如果 pnpm 首次询问构建脚本，只批准 `esbuild`。项目的 `pnpm-workspace.yaml` 不允许其他依赖执行构建脚本。

启动：

```powershell
pnpm --filter szut-club-agent-frontend dev
```

浏览器访问 `http://127.0.0.1:5173`。Dashboard 会请求 FastAPI Statistics API，所有指标和图表均来自 MySQL。

## 测试与构建

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
backend\.venv\Scripts\python.exe -m ruff check backend
pnpm --filter szut-club-agent-frontend exec vitest run
pnpm --filter szut-club-agent-frontend type-check
pnpm --filter szut-club-agent-frontend build
```

## 目录

```text
backend/        FastAPI 后端
frontend/       Vue 3 前端
hermes_plugin/  项目级 Hermes 插件
data/           仿真数据输出与样例
docs/           设计、API、数据库和测试文档
scripts/        Windows 本机辅助脚本
```

开发阶段与完成状态见 `docs/ROADMAP.md`。

## 常见问题

- `3306` 不可连接：在 Windows 服务中启动 `MySQL80`。
- `8000` 被占用：停止旧 FastAPI 进程，不要随意改变前端代理端口。
- `5173` 被占用：停止旧 Vite 进程，保持 `FRONTEND_ORIGIN` 与实际地址一致。
- 前端显示无法连接后端：先访问 `/api/health`，再检查 Vite 代理与 FastAPI 日志。
- Hermes/Ollama 端口未监听：Phase 1～6 不阻塞；Phase 7 会进行专项联调。
