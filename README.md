# 苏州工学院校园社团活动参与统计 Agent

本项目使用 Vue 3、FastAPI、MySQL 与 Hermes Agent 构建校园社团活动数据管理、统计分析和自然语言查询平台。所有业务数据均为固定种子生成的仿真数据；所有统计数字以 MySQL 为唯一来源。

当前系统已完成本机 MySQL、18 张业务表、固定种子仿真数据、Statistics Service、JWT/RBAC、完整业务管理与 Analytics，并已打通 Vue → FastAPI → Hermes → 7 个统计 Tool → MySQL → 本地 Qwen 的 Agent Web 闭环。

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

基础管理页面不依赖 Hermes 与 Ollama；使用 Agent 功能前需启动 AI 服务。

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
- `HERMES_EXECUTABLE`、`HERMES_HOME`（按本机 Hermes Desktop Runtime 实际版本填写）
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

## 启动本地 AI 服务

在 PowerShell 7 中运行：

```powershell
.\scripts\start-ai-services.ps1
.\scripts\check-ai-services.ps1
```

检查结果应显示 Ollama `ready`、模型 `qwen3.5-4b-64k:latest`、`context_length: 65536` 和 Hermes Runtime 版本。Hermes Desktop 0.7.0 当前内置 Runtime 0.19.0，Dashboard 实际地址为 `http://127.0.0.1:9120`。后端使用 Runtime 官方 `--oneshot` 入口，不依赖桌面内部 WebSocket 协议。
安装或更新项目级 Hermes 插件：

```powershell
.\scripts\install-hermes-plugin.ps1
hermes plugins enable szut-club-statistics
```

插件从环境读取 `SZUT_API_BASE_URL`、`AGENT_INTERNAL_KEY` 和每次调用的短期 `SZUT_AGENT_CONTEXT_TOKEN`，不保存数据库密码或用户 JWT。
## 使用校园数据研判台

登录后从左侧“智能分析”进入 `/agent`。可选择学期和校区后直接提问，也可使用预置快捷问题。涉及数量、比率、排行、趋势和分布时，Hermes 会调用项目统计 Tool；页面右侧同步展示 Tool 调用链、结构化数据与受控 ECharts 图表。

会话按当前用户隔离。数据库仅保存用户问题、最终回答、模型名及 Tool 名称/参数/状态摘要；完整 Tool 数据通过单次临时 Trace 返回网页后立即清理，不保存模型隐藏推理。
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
- Agent 显示 Runtime 或模型不可用：运行 `.\scripts\start-ai-services.ps1`，再用 `.\scripts\check-ai-services.ps1` 检查。
- Hermes 提示 Unknown provider：确认 `.env` 的 `HERMES_HOME` 指向 Desktop Runtime 的 `hermes-home`。
