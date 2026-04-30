"""FastAPI 主应用入口"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers import article

# 创建 FastAPI 应用
app = FastAPI(
    title="AI 爆款文章创作器",
    description="基于多智能体编排的 AI 文章创作平台",
    version="0.0.1"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(article.router, prefix="/api/article")

# 用户相关接口（简化版，无需登录）
@app.get("/api/user/get/login")
async def get_login_user():
    """获取登录用户信息（简化版，模拟已登录状态）"""
    return {
        "code": 0,
        "data": {
            "id": 1,
            "userName": "用户",
            "userRole": "normal",
            "quota": -1,  # -1 表示无限制
            "vipTime": None
        },
        "message": "success"
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI 爆款文章创作器 - Python 后端",
        "version": "0.0.1",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8080,
        reload=True
    )
