# Phase 1 Project Initialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可在当前 Windows、本机 MySQL、Hermes Desktop 与 Ollama 环境中启动和测试的 FastAPI + Vue 3 项目骨架。

**Architecture:** 根目录保存跨服务配置和操作文档；`backend` 是同步 SQLAlchemy/PyMySQL 的 FastAPI 模块化单体；`frontend` 是 Vue 3 + TypeScript SPA。Phase 1 只建立配置、健康检查、API Client 和启动状态页，不创建业务表或硬编码业务数据。

**Tech Stack:** Python 3.11、FastAPI、Pydantic Settings、pytest、Vue 3、TypeScript、Vite、Pinia、Vue Router、Axios、Element Plus、Vitest、pnpm、MySQL 8.0.43。

## Global Constraints

- 项目根目录固定为 `D:\文档\实训2026\社团活动参与统计Agent\szut-club-agent`。
- 使用本机 MySQL `127.0.0.1:3306`，不使用 Docker。
- 开发库名 `szut_club_agent`；测试库名 `szut_club_agent_test`。
- 主模型名必须从环境变量读取，默认 `qwen3.5-4b-64k:latest`。
- 不提交 `.env`、密码、JWT Secret、Hermes/DeepSeek API Key。
- 不使用前端硬编码业务假数据。
- 每个任务结束时项目必须保持可启动。

---

### Task 1: Root Contract and Environment Template

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `.env.example`
- Create: `AGENTS.md`

**Interfaces:**
- Consumes: 已确认的本机端口、路径、数据库名和模型名。
- Produces: 后端、前端、脚本和后续 Phase 共用的环境变量契约。

- [ ] **Step 1: Write the root ignore and editor rules**

`.gitignore` 必须忽略：

```gitignore
.env
.env.*
!.env.example
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
frontend/node_modules/
frontend/dist/
frontend/playwright-report/
frontend/test-results/
data/generated/*
!data/generated/.gitkeep
logs/
*.log
.idea/
.vscode/
Thumbs.db
.DS_Store
```

`.editorconfig` 必须统一 UTF-8、LF、末尾换行；Python 使用 4 空格，TypeScript/Vue/JSON/YAML 使用 2 空格。

- [ ] **Step 2: Define the complete environment contract**

创建 `.env.example`：

```dotenv
APP_NAME=SZUT Club Activity Agent
APP_ENV=development
APP_HOST=127.0.0.1
APP_PORT=8000
FRONTEND_ORIGIN=http://127.0.0.1:5173
DATABASE_URL=mysql+pymysql://szut_user:replace-me@127.0.0.1:3306/szut_club_agent?charset=utf8mb4
TEST_DATABASE_URL=mysql+pymysql://szut_user:replace-me@127.0.0.1:3306/szut_club_agent_test?charset=utf8mb4
JWT_SECRET=replace-with-at-least-32-random-bytes
JWT_EXPIRE_MINUTES=60
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=replace-me
SEED_USER_PASSWORD=replace-me
HERMES_BASE_URL=http://127.0.0.1:8642/v1
HERMES_API_KEY=replace-me
AGENT_INTERNAL_KEY=replace-with-at-least-32-random-bytes
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1
LOCAL_LLM_MODEL=qwen3.5-4b-64k:latest
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=replace-me
DEEPSEEK_MODEL=DeepSeek-v4-flash
```

- [ ] **Step 3: Record repository rules**

`AGENTS.md` 明确：分层边界、MySQL 单一数据源、Alembic 强制、Tool 复用 Statistics、禁止 Text-to-SQL、禁止提交密钥、Phase 完成后测试、不得修改 Hermes Core。

- [ ] **Step 4: Verify secrets and generated files are excluded**

Run:

```powershell
git check-ignore .env frontend/node_modules data/generated/example.csv
git check-ignore .env.example
```

Expected: 前三个路径被忽略；`.env.example` 不被忽略。

- [ ] **Step 5: Commit**

```powershell
git add .gitignore .editorconfig .env.example AGENTS.md
git commit -m "chore: define project environment contract"
```

---

### Task 2: FastAPI Application Skeleton

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/pytest.ini`

**Interfaces:**
- Consumes: 根目录 `.env` 中的 `APP_*`、`DATABASE_URL`、模型和 Provider 配置。
- Produces: `app.main:create_app() -> FastAPI`、`GET /api/health`、`Settings`。

- [ ] **Step 1: Write the failing health test**

```python
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_returns_service_identity() -> None:
    settings = Settings(
        app_env="test",
        database_url="mysql+pymysql://user:pass@127.0.0.1/test",
        test_database_url="mysql+pymysql://user:pass@127.0.0.1/test",
        jwt_secret="x" * 32,
        hermes_api_key="test-hermes-key",
        agent_internal_key="x" * 32,
        deepseek_api_key="test-deepseek-key",
    )
    client = TestClient(create_app(settings))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "SZUT Club Activity Agent",
        "environment": "test",
    }
```

- [ ] **Step 2: Create the virtual environment and install bounded dependencies**

`backend/requirements.txt`：

```text
fastapi>=0.115,<1
uvicorn[standard]>=0.34,<1
SQLAlchemy>=2.0,<3
alembic>=1.15,<2
PyMySQL>=1.1,<2
pydantic-settings>=2.7,<3
PyJWT[crypto]>=2.10,<3
pwdlib[argon2]>=0.2,<1
httpx>=0.28,<1
structlog>=25,<26
Faker>=37,<38
```

`backend/requirements-dev.txt`：

```text
-r requirements.txt
pytest>=8,<9
pytest-cov>=6,<7
ruff>=0.11,<1
mypy>=1.15,<2
```

Run:

```powershell
python -m venv backend/.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
backend\.venv\Scripts\python.exe -m pytest backend\tests\test_health.py -q
```

Expected: FAIL because `app.main` does not exist.

- [ ] **Step 3: Implement typed settings**

`backend/app/core/config.py`：

```python
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SZUT Club Activity Agent"
    app_env: Literal["development", "test", "production"] = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    frontend_origin: str = "http://127.0.0.1:5173"
    database_url: str
    test_database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    hermes_base_url: str = "http://127.0.0.1:8642/v1"
    hermes_api_key: str
    agent_internal_key: str
    local_llm_base_url: str = "http://127.0.0.1:11434/v1"
    local_llm_model: str = "qwen3.5-4b-64k:latest"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_api_key: str
    deepseek_model: str = "DeepSeek-v4-flash"

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

测试通过 monkeypatch 设置最小安全环境，不能依赖开发者真实 `.env`。

- [ ] **Step 4: Implement the health route and application factory**

`backend/app/api/health.py`：

```python
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
```

`backend/app/main.py`：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name)
    app.state.settings = resolved_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[resolved_settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router, prefix="/api")
    return app
```

测试显式传入 `app_env="test"` 的 Settings，避免读取开发者真实 `.env` 或污染缓存。

- [ ] **Step 5: Run backend quality gates**

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
backend\.venv\Scripts\python.exe -m ruff check backend
```

Expected: 全部测试通过，Ruff 无错误。

- [ ] **Step 6: Start and smoke-test FastAPI**

```powershell
backend\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --app-dir backend --host 127.0.0.1 --port 8000
```

另一个终端执行：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected: 返回 `status=ok`、服务名和 `development`。

- [ ] **Step 7: Commit**

```powershell
git add backend
git commit -m "feat: initialize FastAPI application"
```

---

### Task 3: Vue Application Skeleton and API Client

**Files:**
- Create: `frontend/` via Vite Vue TypeScript scaffold
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.ts`
- Modify: `frontend/src/App.vue`
- Create: `frontend/src/api/http.ts`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/views/SetupView.vue`
- Create: `frontend/src/types/health.ts`
- Create: `frontend/src/assets/base.css`
- Create: `frontend/src/tests/setup.ts`
- Create: `frontend/src/views/SetupView.spec.ts`
- Modify: `frontend/vite.config.ts`

**Interfaces:**
- Consumes: `GET /api/health` returning `{status, service, environment}`.
- Produces: 可启动 Vue SPA、共享 Axios Client、路由和真实后端连接状态页。

- [ ] **Step 1: Scaffold Vue and install Phase 1 dependencies**

```powershell
pnpm create vite frontend --template vue-ts
pnpm --dir frontend add axios pinia vue-router element-plus @element-plus/icons-vue echarts vue-echarts
pnpm --dir frontend add -D vitest @vue/test-utils happy-dom
```

- [ ] **Step 2: Write the failing setup-page test**

```typescript
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import SetupView from './SetupView.vue'
import { http } from '../api/http'

vi.mock('../api/http', () => ({
  http: { get: vi.fn() },
}))

describe('SetupView', () => {
  it('shows the backend health result', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: { status: 'ok', service: 'SZUT Club Activity Agent', environment: 'test' },
    })

    const wrapper = mount(SetupView)
    await flushPromises()

    expect(wrapper.text()).toContain('后端服务已连接')
    expect(wrapper.text()).toContain('SZUT Club Activity Agent')
  })
})
```

Run:

```powershell
pnpm --dir frontend test -- --run
```

Expected: FAIL because `SetupView.vue` and API Client do not exist.

- [ ] **Step 3: Implement the API contract and page**

`frontend/src/api/http.ts`：

```typescript
import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  timeout: 10_000,
})
```

`SetupView.vue` 在挂载时请求 `/health`，分别展示连接中、连接成功和连接失败，并提供重试按钮。页面只能展示后端返回的服务状态，不包含业务统计假数据。

- [ ] **Step 4: Configure the application shell**

`main.ts` 注册 Pinia、Router、Element Plus 和基础样式。Router 只提供 `/` 到 `SetupView`。Vite 将 `/api` 代理到 `http://127.0.0.1:8000`。`App.vue` 只渲染 `RouterView`。

- [ ] **Step 5: Run frontend quality gates**

在 `package.json` 添加 `test: "vitest"` 和 `type-check: "vue-tsc --build"`。

```powershell
pnpm --dir frontend test -- --run
pnpm --dir frontend type-check
pnpm --dir frontend build
```

Expected: 测试、类型检查和生产构建全部通过。

- [ ] **Step 6: Commit**

```powershell
git add frontend
git commit -m "feat: initialize Vue application"
```

---

### Task 4: Windows Environment Check and Startup Documentation

**Files:**
- Create: `scripts/check-environment.ps1`
- Create: `README.md`
- Create: `data/generated/.gitkeep`
- Create: `data/samples/.gitkeep`
- Create: `hermes_plugin/.gitkeep`

**Interfaces:**
- Consumes: 已确认的 Python、Node、MySQL、Hermes Desktop、Ollama 路径和端口。
- Produces: 可重复执行的只读环境检查，以及 Phase 1 完整启动说明。

- [ ] **Step 1: Implement the read-only environment checker**

`scripts/check-environment.ps1` 使用 `Get-Command`、`Get-Service MySQL80`、`Test-NetConnection` 和 `Test-Path` 检查：

```text
Python >= 3.11
Node >= 22
pnpm 可用
MySQL80 正在运行
127.0.0.1:3306 可连接
D:\Hermes\Hermes Agent CN Desktop\hermes-agent-cn-desktop.exe 存在
D:\ollama-windows-amd64\ollama.exe 存在
D:\ollama_custom\Modelfile 存在
qwen3.5-4b-64k:latest manifest 存在
```

每项输出 `[PASS]`、`[WARN]` 或 `[FAIL]`；必需项失败时退出码为 1。Hermes/Ollama 尚未启动在 Phase 1 只输出 WARN，因为它们在 Phase 7 才成为启动前置条件。

- [ ] **Step 2: Run the checker**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check-environment.ps1
```

Expected: Python、Node、pnpm、MySQL、程序文件和模型 manifest 为 PASS；未监听的 Hermes/Ollama 端口最多为 WARN；退出码为 0。

- [ ] **Step 3: Write the complete Phase 1 README**

README 必须包含：项目边界、目录、前置环境、复制 `.env.example` 为 `.env`、安全生成 Secret、创建两个数据库与最小权限 MySQL 用户、创建虚拟环境、安装依赖、启动后端、启动前端、运行测试和常见端口冲突排查。

创建数据库的 SQL 必须显式限定为：

```sql
CREATE DATABASE IF NOT EXISTS szut_club_agent
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE DATABASE IF NOT EXISTS szut_club_agent_test
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
```

README 不包含真实密码或 Key。

- [ ] **Step 4: Run the complete Phase 1 regression**

```powershell
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
backend\.venv\Scripts\python.exe -m ruff check backend
pnpm --dir frontend test -- --run
pnpm --dir frontend type-check
pnpm --dir frontend build
powershell -ExecutionPolicy Bypass -File scripts\check-environment.ps1
git status --short
```

Expected: 所有自动化检查通过；`git status --short` 只显示本任务待提交文件。

- [ ] **Step 5: Commit**

```powershell
git add README.md scripts data hermes_plugin docs/ROADMAP.md docs/superpowers/plans/2026-08-22-phase-1-project-initialization.md
git commit -m "docs: add Phase 1 setup workflow"
```

## Phase 1 Completion Gate

完成标准：

- 后端 `/api/health` 可访问且测试通过。
- 前端可访问并真实显示后端连接状态。
- `.env` 和所有密钥均未进入 Git。
- 本机 MySQL、Hermes、Ollama 路径检查结果可复现。
- 后端测试、Ruff、前端测试、类型检查、生产构建全部通过。
- 进入 Phase 2 前，项目可由 README 从干净终端重新启动。
