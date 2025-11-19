# LightSource

简洁的 AI 媒资生成与管理示例：后端 FastAPI + SQLAlchemy，前端 Vue 3 + Pinia + Vite。涵盖登录、任务、资源、提供商、管理员、钱包与偏好设置，采用 HTTP 轮询与静态文件存储。

## 特性
- 后端 API（统一前缀 `/api`）：`/api/auth`、`/api/providers`、`/api/jobs`、`/api/assets`、`/api/v1/images`、`/api/v1/videos`、`/api/billing`、`/api/preferences`、`/api/admin`、`/api/metrics`、`/api/health`
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

## 接口层（Providers）
- 位置：`app/interface/`，封装与外部模型/视频服务的交互，统一调用与返回结构。
- 抽象协议：`Provider` 定义 `generate(request, job)`（`app/interface/base.py:8–10`）。
- 适配器注册：
  - `resolve_adapter(name)` 返回具体适配器（`app/interface/registry.py:96–105`）。
  - `QwenAdapter` 图像生成/编辑（`app/interface/registry.py:11–16`）。
  - `FluxAdapter` 图像生成（`app/interface/registry.py:19–23`）。
  - `MajicFlusAdapter` 图像生成（`app/interface/registry.py:24–27`）。
  - `Sora2Adapter` 视频创建/查询/生成（`app/interface/registry.py:29–93`）。
- Qwen（ModelScope）：
  - 模型映射 `MODEL_MAP`（`app/interface/qwen.py:16–19`）。
  - 文生图 `generate_image`（`app/interface/qwen.py:54–115`）。
  - 以图编辑 `edit_image`（`app/interface/qwen.py:118–186`）。
- Flux（ModelScope）：文生图 `generate_image`（`app/interface/flux.py:32–56`）。
- MajicFlus（ModelScope）：文生图 `generate_image`（`app/interface/majicflus.py:32–56`）。
- Sora2（视频）：
  - 创建视频 `create_video`（`app/interface/sora2.py:48–92`）。
  - 查询视频 `get_video`（`app/interface/sora2.py:95–129`）。
  - 文生视频 `generate_video`（`app/interface/sora2.py:132–167`）。
  - 以图生视频 `image_to_video`（`app/interface/sora2.py:170–205`）。
- 生成编排：在 `app/services/generation.py` 中按 Job 类型调用适配器：
  - 解析适配器并分发任务（`app/services/generation.py:49–51, 67–88`）。
  - Sora2 视频创建与元信息写入（`app/services/generation.py:100–127`）。
  - 查询视频详情并填充结果（`app/services/generation.py:163–184`）。

## 快速开始
- 后端
  - `python -m venv .venv && .venv\\Scripts\\activate`
  - `pip install -r requirements.txt`
  - 配置 `.env`（示例键见下）并运行：`uvicorn app.main:app --reload`
  - 初始化数据库与默认数据：`python scripts/init_db.py`
- 前端
  - `cd lightsource-vue && npm i`
  - `npm run dev`（默认 `VITE_API_BASE_URL=http://127.0.0.1:8000`）

## Docker
- 构建：`docker build -t lightsource .`
- 运行（Windows PowerShell）：
  - `docker run -p 8000:8000 -v %CD%/storage/media:/app/storage/media --env-file .env lightsource`
- 运行（Linux/macOS）：
  - `docker run -p 8000:8000 -v $(pwd)/storage/media:/app/storage/media --env-file .env lightsource`
- 默认容器环境：
  - `DATABASE_URL=postgresql+psycopg2://postgres:postgres@host.docker.internal:5432/lightsource`
  - 如需自定义，使用 `--env-file .env` 或 `-e DATABASE_URL=...` 覆盖。
  - Linux 下如需连接宿主机数据库，可添加 `--add-host=host.docker.internal:host-gateway` 或改用宿主机 IP。
  - 媒资目录挂载到 `storage/media/` 保持持久化。
  - 前端打包目录 `lightsource-vue/dist` 下的静态资源通过后端挂载：根路径 `/` 为首页，`/assets/*` 提供静态文件。

## 前端与后端路由约定
- 前端：根路径 `/` 渲染打包后的 `index.html`；路由如 `/assets`、`/generator`、`/settings`。
- 静态：构建资源位于 `/assets/*`（由后端挂载）。
- 后端 API：统一前缀 `/api`，例如：
  - 认证：`/api/auth/*`
  - 资产：`/api/assets/*`
  - 任务：`/api/jobs/*`
  - 生成：`/api/v1/images`、`/api/v1/videos`
  - 管理：`/api/admin/*`
  - 指标与健康：`/api/metrics`、`/api/health`

## 前端 API 地址配置
- 默认自动跟随主机：`protocol://hostname:8000`，请求统一加 `/api` 前缀。
- 如需跨域或不同端口/域名，在前端设置 `VITE_API_BASE_URL`（例如 `https://api.example.com`）。
- 代码位置：`lightsource-vue/src/api/client.ts`。

## 环境变量
- 必需：`DATABASE_URL`、`STORAGE_BASE`、`CORS_ORIGINS`、`JWT_SECRET`、`JWT_ACCESS_MINUTES`、`JWT_REFRESH_MINUTES`、`RATE_LIMIT_PER_MINUTE`、`BURST_LIMIT`
- 可选：`PUBLIC_API_KEY`、`EXT_IMAGE_UPLOAD_AUTH_KEY`

## 许可证
- 见 `LICENSE`
