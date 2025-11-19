# LightSource

简洁的 AI 媒资生成与管理示例：后端 FastAPI + SQLAlchemy，前端 Vue 3 + Pinia + Vite。涵盖登录、任务、资源、提供商、管理员、钱包与偏好设置，采用 HTTP 轮询与静态文件存储。

```mermaid
flowchart LR
  U[User] --> F[Vue 3 + Pinia + Vite]
  F --> A[/FastAPI/]
  A -->|JWT| Auth[Auth]
  A --> Jobs[Jobs: Images & Videos]
  A --> Assets[Assets]
  A --> Providers[Providers]
  A --> Admin[Admin]
  A --> Billing[Wallet]
  A --> Prefs[Preferences]
  A --> Metrics[Metrics & Rate Limit]
  A --> Media[/StaticFiles /media]
  A --> DB[(PostgreSQL)]
  Media --> Storage[storage/media]
```

## 特性
- 后端 API：`/auth`、`/providers`、`/jobs`、`/assets`、`/v1/images`、`/v1/videos`、`/billing`、`/preferences`、`/admin`、`/metrics`、`/health`
- 速率限制与跨域：中间件配置与 CORS 列表（参考 `app/main.py` 与 `app/config.py`）
- 媒资静态服务：`/media` 映射到 `storage/media/`

## 截图
![生成器界面](/generator.png)
![资源库界面](/library.png)

## 目录
- `app/` 后端代码（FastAPI、SQLAlchemy、Pydantic）
- `lightsource-vue/` 前端代码（Vite、Vue 3、Pinia、Vue Router）
- `storage/media/` 生成与上传媒资目录（已忽略）
- `scripts/` 初始化与工具脚本
- `alembic/` 数据库迁移（已忽略）

## 快速开始
- 后端
  - `python -m venv .venv && .venv\\Scripts\\activate`
  - `pip install -r requirements.txt`
  - 配置 `.env`（示例键见下）并运行：`uvicorn app.main:app --reload`
  - 初始化数据库与默认数据：`python scripts/init_db.py`
- 前端
  - `cd lightsource-vue && npm i`
  - `npm run dev`（默认 `VITE_API_BASE_URL=http://127.0.0.1:8000`）

## 环境变量
- 必需：`DATABASE_URL`、`STORAGE_BASE`、`CORS_ORIGINS`、`JWT_SECRET`、`JWT_ACCESS_MINUTES`、`JWT_REFRESH_MINUTES`、`RATE_LIMIT_PER_MINUTE`、`BURST_LIMIT`
- 可选：`PUBLIC_API_KEY`、`EXT_IMAGE_UPLOAD_AUTH_KEY`

## 许可证
- 见 `LICENSE`