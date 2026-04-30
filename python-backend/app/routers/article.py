"""文章路由"""

import asyncio
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.common import BaseResponse, DeleteRequest
from app.schemas.article import (
    ArticleAiModifyOutlineRequest,
    ArticleConfirmOutlineRequest,
    ArticleConfirmTitleRequest,
    ArticleCreateRequest,
    ArticleQueryRequest,
    ArticleVO,
)
from app.services.article_async_service import article_async_service
from app.managers.sse_manager import sse_emitter_manager
from app.exceptions import ErrorCode, throw_if

router = APIRouter(prefix="/article", tags=["文章管理"])

# 内存存储文章状态
article_states = {}


@router.post("/create", response_model=BaseResponse[str])
async def create_article(
    request: ArticleCreateRequest,
):
    """创建文章任务"""
    throw_if(
        not request.topic or not request.topic.strip(),
        ErrorCode.PARAMS_ERROR,
        "选题不能为空"
    )
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 存储文章状态
    article_states[task_id] = {
        "topic": request.topic,
        "style": request.style,
        "enabled_image_methods": request.enabled_image_methods
    }
    
    # 异步执行阶段1：生成标题方案
    asyncio.create_task(
        article_async_service.execute_phase1(
            task_id,
            request.topic,
            request.style,
        )
    )
    
    return BaseResponse.success(data=task_id, message="任务创建成功")


@router.get("/progress/{task_id}")
async def get_progress(
    task_id: str,
):
    """SSE 进度推送"""
    throw_if(
        not task_id or not task_id.strip(),
        ErrorCode.PARAMS_ERROR,
        "任务ID不能为空"
    )
    
    # 检查任务是否存在
    throw_if(
        task_id not in article_states,
        ErrorCode.PARAMS_ERROR,
        "任务不存在"
    )
    
    # 创建 SSE Emitter
    return sse_emitter_manager.create_emitter(task_id)


@router.get("/{task_id}", response_model=BaseResponse[ArticleVO])
async def get_article(
    task_id: str,
):
    """获取文章详情"""
    throw_if(
        not task_id or not task_id.strip(),
        ErrorCode.PARAMS_ERROR,
        "任务ID不能为空"
    )
    
    # 检查任务是否存在
    throw_if(
        task_id not in article_states,
        ErrorCode.PARAMS_ERROR,
        "任务不存在"
    )
    
    # 返回基本信息
    article_data = article_states[task_id]
    article_vo = ArticleVO(
        id=task_id,
        mainTitle=article_data.get("mainTitle", ""),
        subTitle=article_data.get("subTitle", ""),
        content=article_data.get("content", ""),
        fullContent=article_data.get("fullContent", ""),
        images=article_data.get("images", []),
        createTime=article_data.get("createTime", None),
        updateTime=article_data.get("updateTime", None)
    )
    
    return BaseResponse.success(data=article_vo)


@router.post("/confirm-title", response_model=BaseResponse[None])
async def confirm_title(
    request: ArticleConfirmTitleRequest,
):
    """确认标题并输入补充描述"""
    # 检查任务是否存在
    throw_if(
        request.task_id not in article_states,
        ErrorCode.PARAMS_ERROR,
        "任务不存在"
    )
    
    # 更新文章状态
    article_states[request.task_id].update({
        "mainTitle": request.selected_main_title,
        "subTitle": request.selected_sub_title,
        "userDescription": request.user_description
    })
    
    # 异步执行阶段2
    asyncio.create_task(article_async_service.execute_phase2(request.task_id))
    return BaseResponse.success(data=None)


@router.post("/confirm-outline", response_model=BaseResponse[None])
async def confirm_outline(
    request: ArticleConfirmOutlineRequest,
):
    """确认大纲"""
    # 检查任务是否存在
    throw_if(
        request.task_id not in article_states,
        ErrorCode.PARAMS_ERROR,
        "任务不存在"
    )
    
    # 更新文章状态
    article_states[request.task_id]["outline"] = request.outline
    
    # 异步执行阶段3
    asyncio.create_task(article_async_service.execute_phase3(request.task_id))
    return BaseResponse.success(data=None)
