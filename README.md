# AI 爆款文章创作器（个人版）

基于多智能体编排的 AI 文章创作平台，支持一键生成高质量爆款文章。

## 项目简介

本项目是一个简洁版的 AI 文章创作工具，去除了原项目的 VIP 和付费功能，专为个人用户打造。保留核心的多智能体协作系统，让用户可以轻松创作优质内容。

## 技术架构

### 前端
- **框架**：Vue 3.5 + TypeScript
- **构建工具**：Vite
- **UI 组件库**：Ant Design Vue
- **状态管理**：Pinia
- **路由**：Vue Router

### 后端
- **框架**：Python FastAPI
- **异步任务**：asyncio
- **实时通信**：SSE (Server-Sent Events)

### 核心特性
- 多智能体协调系统（标题生成、大纲生成、正文生成、配图分析、图文合成）
- 流式输出，实时展示创作过程
- 多种配图方式支持（Pexels、Mermaid、Iconify 等）
- 字数选择（1000/2000/5000/8000+ 字）
- 文章风格选择
- Markdown 渲染

## 项目结构

```
ai-passage-creator/
├── frontend/                    # 前端项目
│   ├── src/
│   │   ├── api/               # API 接口
│   │   ├── components/        # 公共组件
│   │   ├── pages/             # 页面组件
│   │   ├── stores/            # 状态管理
│   │   ├── utils/            # 工具函数
│   │   └── router/            # 路由配置
│   └── package.json
│
├── python-backend/             # Python 后端
│   ├── routers/              # 路由模块
│   ├── services/             # 服务层
│   ├── main.py              # 主入口
│   └── requirements.txt
│
└── README.md
```

## 快速开始

### 环境要求

- Node.js 22+
- Python 3.8+

### 安装依赖

```bash
# 前端依赖
cd frontend
npm install

# 后端依赖
cd python-backend
pip install -r requirements.txt
```

### 启动服务

```bash
# 启动后端（端口 8080）
cd python-backend
python -m uvicorn main:app --reload --port 8080

# 启动前端（端口 5173）
cd frontend
npm run dev
```

### 配置 API Key

在 `python-backend/` 目录下创建 `.env` 文件或修改配置文件，填入以下 API Key：

```env
PEXELS_API_KEY=your_pexels_api_key
NANO_BANANA_API_KEY=your_nano_banana_api_key
```

## 功能说明

### 文章创作流程

1. **输入选题** - 输入想要创作的文章主题
2. **选择风格** - 可选：科技风格、情感风格、教育风格、轻松幽默
3. **选择字数** - 可选：1000字（短篇）、2000字（中篇）、5000字（长篇）、8000字+（超长篇）
4. **选择配图方式** - 可选：Pexels 图片、Mermaid 图表、Iconify 图标等
5. **AI 生成** - 自动完成标题、大纲、正文、配图的全流程创作

### 大纲编辑

生成大纲后，用户可以：
- 手动编辑章节标题和要点
- 拖动调整章节顺序
- 添加/删除章节和要点
- 使用 AI 助手智能修改大纲

### 多智能体协作

系统包含 5 个专业智能体：
- **标题生成智能体** - 分析选题，生成吸引眼球的标题
- **大纲生成智能体** - 构建文章结构，理清逻辑脉络
- **正文生成智能体** - 流式生成高质量文章内容
- **配图分析智能体** - 智能分析配图需求和位置
- **图文合成智能体** - 自动匹配图片并插入正文

## API 接口

### 创建文章任务
```
POST /article/create
Body: {
  "topic": "文章选题",
  "style": "文章风格（可选）",
  "wordCount": 目标字数,
  "enabledImageMethods": ["配图方式"]
}
```

### 确认标题
```
POST /article/confirm-title
Body: {
  "taskId": "任务ID",
  "selectedMainTitle": "主标题",
  "selectedSubTitle": "副标题"
}
```

### 确认大纲
```
POST /article/confirm-outline
Body: {
  "taskId": "任务ID"
}
```

### SSE 进度订阅
```
GET /article/progress/{task_id}
```

## License

MIT License
