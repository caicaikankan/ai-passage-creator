"""文章异步任务服务"""

import json
import logging
from typing import Any, Dict, Optional

from app.schemas.article import ArticleState, OutlineSection, OutlineResult, TitleResult
from app.models.enums import ArticlePhaseEnum, ArticleStatusEnum, SseMessageTypeEnum
from app.services.article_agent_service import ArticleAgentService
from app.managers.sse_manager import sse_emitter_manager

logger = logging.getLogger(__name__)

# 从路由模块导入全局文章状态存储
from app.routers.article import article_states


class ArticleAsyncService:
    """文章异步任务服务"""

    async def execute_phase1(
        self,
        task_id: str,
        topic: str,
        style: Optional[str] = None,
    ):
        """阶段1：异步生成标题方案"""
        logger.info("阶段1异步任务开始, taskId=%s, topic=%s, style=%s", task_id, topic, style)
        article_agent_service = ArticleAgentService()

        try:
            # 检查任务是否存在
            if task_id not in article_states:
                raise RuntimeError("任务不存在")

            state = ArticleState()
            state.task_id = task_id
            state.topic = topic
            state.style = style

            await article_agent_service.execute_phase1_generate_titles(
                state,
                lambda message: self._handle_agent_message(task_id, message, state)
            )

            # 存储标题选项
            article_states[task_id]["titleOptions"] = state.title_options

            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.TITLES_GENERATED,
                {
                    "titleOptions": [
                        item.model_dump(by_alias=True) for item in (state.title_options or [])
                    ]
                },
            )

            logger.info("阶段1异步任务完成, taskId=%s", task_id)
        except Exception as e:
            logger.error("阶段1异步任务失败, taskId=%s, error=%s", task_id, e)
            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.ERROR,
                {"message": str(e)}
            )
            sse_emitter_manager.complete(task_id)

    async def execute_phase2(self, task_id: str):
        """阶段2：异步生成大纲"""
        logger.info("阶段2异步任务开始, taskId=%s", task_id)
        article_agent_service = ArticleAgentService()

        try:
            # 检查任务是否存在
            if task_id not in article_states:
                raise RuntimeError("任务不存在")

            article_data = article_states[task_id]
            state = ArticleState()
            state.task_id = task_id
            state.style = article_data.get("style")
            state.user_description = article_data.get("userDescription")
            state.title = TitleResult(
                mainTitle=article_data.get("mainTitle"),
                subTitle=article_data.get("subTitle"),
            )

            await article_agent_service.execute_phase2_generate_outline(
                state,
                lambda message: self._handle_agent_message(task_id, message, state)
            )

            # 存储大纲
            article_states[task_id]["outline"] = [
                item.model_dump() for item in (state.outline.sections if state.outline else [])
            ]

            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.OUTLINE_GENERATED,
                {
                    "outline": [
                        item.model_dump() for item in (state.outline.sections if state.outline else [])
                    ]
                },
            )
            logger.info("阶段2异步任务完成, taskId=%s", task_id)
        except Exception as e:
            logger.error("阶段2异步任务失败, taskId=%s, error=%s", task_id, e)
            self._send_sse_message(task_id, SseMessageTypeEnum.ERROR, {"message": str(e)})
            sse_emitter_manager.complete(task_id)

    async def execute_phase3(self, task_id: str):
        """阶段3：异步生成正文与配图"""
        logger.info("阶段3异步任务开始, taskId=%s", task_id)
        article_agent_service = ArticleAgentService()

        try:
            # 检查任务是否存在
            if task_id not in article_states:
                raise RuntimeError("任务不存在")

            article_data = article_states[task_id]
            outline_data = article_data.get("outline", [])
            state = ArticleState()
            state.task_id = task_id
            state.style = article_data.get("style")
            state.enabled_image_methods = article_data.get("enabled_image_methods")
            state.title = TitleResult(
                mainTitle=article_data.get("mainTitle"),
                subTitle=article_data.get("subTitle"),
            )
            state.outline = OutlineResult(
                sections=[OutlineSection(**item) for item in outline_data]
            )

            await article_agent_service.execute_phase3_generate_content(
                state,
                lambda message: self._handle_agent_message(task_id, message, state)
            )

            # 存储文章内容
            article_states[task_id].update({
                "content": state.content,
                "fullContent": state.full_content,
                "images": [img.model_dump(by_alias=True) for img in (state.images or [])]
            })

            self._send_sse_message(
                task_id,
                SseMessageTypeEnum.ALL_COMPLETE,
                {"taskId": task_id}
            )
            sse_emitter_manager.complete(task_id)
            logger.info("阶段3异步任务完成, taskId=%s", task_id)
        except Exception as e:
            logger.error("阶段3异步任务失败, taskId=%s, error=%s", task_id, e)
            self._send_sse_message(task_id, SseMessageTypeEnum.ERROR, {"message": str(e)})
            sse_emitter_manager.complete(task_id)

    def _handle_agent_message(self, task_id: str, message: str, state: ArticleState):
        """处理智能体消息并推送"""
        data = self._build_message_data(message, state)
        if data is not None:
            sse_emitter_manager.send(task_id, json.dumps(data, ensure_ascii=False))
    
    def _build_message_data(self, message: str, state: ArticleState) -> Dict[str, Any]:
        """构建消息数据"""
        # 处理流式消息（带冒号分隔符）
        streaming_prefix2 = SseMessageTypeEnum.AGENT2_STREAMING.get_streaming_prefix()
        streaming_prefix3 = SseMessageTypeEnum.AGENT3_STREAMING.get_streaming_prefix()
        image_complete_prefix = SseMessageTypeEnum.IMAGE_COMPLETE.get_streaming_prefix()
        
        if message.startswith(streaming_prefix2):
            return self._build_streaming_data(
                SseMessageTypeEnum.AGENT2_STREAMING,
                message[len(streaming_prefix2):]
            )
        
        if message.startswith(streaming_prefix3):
            return self._build_streaming_data(
                SseMessageTypeEnum.AGENT3_STREAMING,
                message[len(streaming_prefix3):]
            )
        
        if message.startswith(image_complete_prefix):
            image_json = message[len(image_complete_prefix):]
            return self._build_image_complete_data(image_json)
        
        # 处理完成消息（枚举值）
        return self._build_complete_message_data(message, state)
    
    def _build_streaming_data(self, type_enum: SseMessageTypeEnum, content: str) -> Dict[str, Any]:
        """构建流式输出数据"""
        return {
            "type": type_enum.value,
            "content": content
        }
    
    def _build_image_complete_data(self, image_json: str) -> Dict[str, Any]:
        """构建图片完成数据"""
        return {
            "type": SseMessageTypeEnum.IMAGE_COMPLETE.value,
            "image": json.loads(image_json)
        }
    
    def _build_complete_message_data(self, message: str, state: ArticleState) -> Dict[str, Any]:
        """构建完成消息数据"""
        data = {}
        
        if message == SseMessageTypeEnum.AGENT1_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT1_COMPLETE.value
            data["titleOptions"] = [
                item.model_dump(by_alias=True) for item in (state.title_options or [])
            ]
        elif message == SseMessageTypeEnum.AGENT2_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT2_COMPLETE.value
            data["outline"] = [s.model_dump() for s in state.outline.sections] if state.outline else []
        elif message == SseMessageTypeEnum.AGENT3_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT3_COMPLETE.value
        elif message == SseMessageTypeEnum.AGENT4_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT4_COMPLETE.value
            data["imageRequirements"] = [
                req.model_dump(by_alias=True) for req in state.image_requirements
            ] if state.image_requirements else []
        elif message == SseMessageTypeEnum.AGENT5_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.AGENT5_COMPLETE.value
            data["images"] = [
                img.model_dump(by_alias=True) for img in state.images
            ] if state.images else []
        elif message == SseMessageTypeEnum.MERGE_COMPLETE.value:
            data["type"] = SseMessageTypeEnum.MERGE_COMPLETE.value
            data["fullContent"] = state.full_content
        else:
            return None
        
        return data
    
    def _send_sse_message(
        self,
        task_id: str,
        type_enum: SseMessageTypeEnum,
        additional_data: Dict[str, Any]
    ):
        """发送 SSE 消息"""
        data = {"type": type_enum.value}
        data.update(additional_data)
        sse_emitter_manager.send(task_id, json.dumps(data, ensure_ascii=False))


# 全局单例
article_async_service = ArticleAsyncService()
