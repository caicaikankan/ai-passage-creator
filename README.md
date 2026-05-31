# AI 文章创作器（个人精简版）

基于多智能体编排的 AI 文章创作平台，支持一键生成不同字数、不同风格的长文。

> 本仓库去除了原始项目的 VIP、付费、配图存储、Java/Go 多后端等功能，仅保留可独立运行的最小核心：Vue 3 前端 + Python FastAPI 后端，对接火山引擎方舟（Ark）大模型 API。

## 技术栈

- **前端**：Vue 3 + TypeScript + Vite + Ant Design Vue + Pinia
- **后端**：Python 3.10+ + FastAPI + SSE（流式输出）
- **大模型**：火山引擎方舟 `ark-code-latest`（Coding Plan）

## 目录结构

```
ai-passage-creator/
├── frontend/              # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── api/           # 自动生成的接口层
│   │   ├── components/    # 公共组件
│   │   ├── pages/         # 页面（首页 / 文章创作 / 历史 / 登录 等）
│   │   ├── stores/        # Pinia 状态
│   │   ├── router/        # 路由
│   │   └── utils/         # SSE / Markdown / 时间等工具
│   └── package.json
├── python-backend/        # FastAPI 后端
│   ├── main.py            # 单文件入口：所有路由 + 多智能体调度
│   ├── requirements.txt
│   └── .env.example       # 复制为 .env 并填入方舟 API Key
└── README.md
```

## 快速开始

### 环境要求

- Node.js 22+
- Python 3.10+
- 一个火山引擎方舟 API Key（Coding Plan 或按量付费均可）

### 1. 安装依赖

```bash
# 前端
cd frontend
npm install

# 后端
cd ../python-backend
pip install -r requirements.txt
```

### 2. 配置方舟 API Key

```bash
cd python-backend
cp .env.example .env
# 编辑 .env，把 ARK_API_KEY 替换为你的真实 Key
```

> 申请地址：https://www.volcengine.com/product/ark
> 若使用 Coding Plan，请保持 `ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3`，**不要**使用 `/api/v3`（会产生额外费用）。

### 3. 启动服务

```bash
# 终端 1：启动后端（端口 8567）
cd python-backend
python -m uvicorn main:app --reload --port 8567

# 终端 2：启动前端（端口 5173）
cd frontend
npm run dev
```

打开浏览器访问 http://localhost:5173/ 即可。

> 前端 Vite 已配置代理：所有 `/api/*` 请求会自动转发到后端的 `http://localhost:8567`，无需额外配置。

## 创作流程

1. **输入选题** —— 例如「儿童节亲子陪伴」「AI 提示词工程入门」
2. **选择风格 / 字数 / 配图方式**
   - 风格：科技、情感、教育、轻松幽默
   - 字数：1000 / 2000 / 5000 / 8000+
3. **AI 自动生成 3 个标题方案**，挑选一个
4. **AI 生成大纲**，可手动拖拽编辑章节、要点
5. **流式生成正文**，SSE 实时推送
6. **完成 → 一键复制全文**

## 核心特性

- ✅ 真正的流式输出（SSE），可见 AI 实时打字
- ✅ 字数动态控制：根据所选目标字数动态计算 `max_tokens` 与超时时间，最大支持约 8000 字稳定输出
- ✅ 大纲可编辑：在确认前可任意调整章节结构
- ✅ 多智能体编排：标题智能体 → 大纲智能体 → 正文智能体

## 主要接口

| 接口 | 说明 |
|---|---|
| `POST /api/article/create` | 创建文章任务，开始标题生成 |
| `POST /api/article/confirm-title` | 用户确认标题，触发大纲生成 |
| `POST /api/article/confirm-outline` | 用户确认大纲，触发正文流式生成 |
| `GET  /api/article/progress/{task_id}` | SSE 长连接，订阅创作进度 |

## 安全提示

- `python-backend/.env` 已被 `.gitignore` 忽略，**不要把真实 API Key 提交到 GitHub**
- 若不慎泄露 Key，立刻去方舟控制台轮换：https://console.volcengine.com/ark

## License

MIT
