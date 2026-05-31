"""文章路由 - 简化版（无数据库，专注文章生成）"""

import asyncio
import json
import os
import uuid
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储文章状态
article_states = {}
sse_connections = {}

# SSE 连接
@app.get("/api/article/progress/{task_id}")
async def progress(task_id: str):
    """SSE 连接"""
    async def event_generator():
        queue = asyncio.Queue()
        sse_connections[task_id] = queue
        try:
            while True:
                message = await queue.get()
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            if task_id in sse_connections:
                del sse_connections[task_id]
            raise
    
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
    }
    return StreamingResponse(event_generator(), headers=headers)


# 创建文章任务
@app.post("/api/article/create")
async def create_article(request: Request):
    """创建文章任务"""
    data = await request.json()
    topic = data.get("topic")
    style = data.get("style", "")
    word_count = data.get("wordCount", 1000)

    task_id = str(uuid.uuid4())

    article_states[task_id] = {
        "topic": topic,
        "style": style,
        "wordCount": word_count,
        "status": "PROCESSING"
    }

    asyncio.create_task(generate_article(task_id, topic, style, word_count))

    return {"code": 0, "data": task_id, "message": "任务创建成功"}


# 确认标题
@app.post("/api/article/confirm-title")
async def confirm_title(request: Request):
    """确认标题"""
    data = await request.json()
    task_id = data.get("taskId")
    selected_main_title = data.get("selectedMainTitle")
    selected_sub_title = data.get("selectedSubTitle")

    if task_id in article_states:
        article_states[task_id]["mainTitle"] = selected_main_title
        article_states[task_id]["subTitle"] = selected_sub_title
        article_states[task_id]["status"] = "TITLE_CONFIRMED"
        asyncio.create_task(generate_outline(task_id))

    return {"code": 0, "data": None, "message": "标题确认成功"}


# 确认大纲
@app.post("/api/article/confirm-outline")
async def confirm_outline(request: Request):
    """确认大纲"""
    data = await request.json()
    task_id = data.get("taskId")

    if task_id in article_states:
        article_states[task_id]["status"] = "OUTLINE_CONFIRMED"
        asyncio.create_task(generate_content(task_id))

    return {"code": 0, "data": None, "message": "大纲确认成功"}


# 获取文章列表
@app.post("/api/article/list")
async def list_articles(request: Request):
    """获取文章列表"""
    return {
        "code": 0,
        "data": {"records": [], "total": 0, "pageNum": 1, "pageSize": 10},
        "message": "success"
    }


# 用户相关接口（简化版，用于支持前端页面）
@app.get("/api/user/get/login")
async def get_login_user():
    """获取当前登录用户（简化版）"""
    return {
        "code": 0,
        "data": {
            "id": 1,
            "userName": "guest",
            "userRole": "default"
        },
        "message": "success"
    }


@app.post("/api/user/login")
async def login(request: Request):
    """登录（简化版）"""
    return {"code": 0, "data": None, "message": "登录成功"}


@app.post("/api/user/logout")
async def logout(request: Request):
    """登出（简化版）"""
    return {"code": 0, "data": None, "message": "登出成功"}


async def send_sse(task_id: str, message: dict):
    """发送 SSE 消息"""
    if task_id in sse_connections:
        await sse_connections[task_id].put(json.dumps(message, ensure_ascii=False))


async def call_ark_api(messages: list, stream: bool = False, max_tokens: int = 4000):
    """调用方舟 API"""
    api_key = os.getenv("ARK_API_KEY", "")
    base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3")
    model = os.getenv("ARK_MODEL", "ark-code-latest")

    print(f"[DEBUG] API Key loaded: {api_key[:10]}..." if api_key else "[DEBUG] API Key not loaded")
    print(f"[DEBUG] Base URL: {base_url}")
    print(f"[DEBUG] Model: {model}")

    if not api_key:
        print("[ERROR] ARK_API_KEY not set")
        raise ValueError("未配置方舟 API Key")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": stream
    }

    try:
        print(f"[DEBUG] Calling API: {base_url}/chat/completions")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            print(f"[DEBUG] API Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"[DEBUG] API Response received, length: {len(json.dumps(result))}")
            return result
    except Exception as e:
        print(f"[ERROR] API call failed: {str(e)}")
        raise


async def generate_article(task_id: str, topic: str, style: str, word_count: int):
    """生成文章主流程"""
    try:
        await send_sse(task_id, {"type": "PHASE", "phase": 1, "message": "正在生成标题..."})

        title_prompt = f"""根据以下选题和风格，生成3个吸引人的文章标题方案。

选题：{topic}
风格：{style if style else '通用'}

输出格式（直接输出，不要有其他说明）：
【主标题1】副标题1
【主标题2】副标题2
【主标题3】副标题3

要求：
- 主标题要简洁有力，吸引眼球
- 副标题要补充说明，增加信息量
- 3个方案要有差异化，覆盖不同角度
- 直接输出标题，不需要解释或追问"""

        result = await call_ark_api(
            messages=[{"role": "user", "content": title_prompt}],
            max_tokens=800
        )

        titles_text = result["choices"][0]["message"]["content"]
        print(f"[DEBUG] AI 返回的标题文本:\n{titles_text}")
        
        # 解析标题文本，转换为前端期望的格式
        title_options = []
        lines = titles_text.strip().split('\n')
        
        current_main = ""
        current_sub = ""
        
        for line in lines:
            line = line.strip()
            if line:
                # 移除序号（如 "1."）
                if line[0].isdigit() and (line[1] == '.' or line[1] == '、'):
                    line = line[2:].strip()
                
                # 检查是否是新的主标题（包含【】）
                if '【' in line and '】' in line:
                    # 如果之前有未保存的标题，先保存
                    if current_main:
                        title_options.append({"mainTitle": current_main, "subTitle": current_sub})
                    
                    # 提取新的主标题和副标题
                    main_part = line.split('【')[1].split('】')[0]
                    sub_part = line.split('】')[1].strip() if len(line.split('】')) > 1 else ''
                    
                    # 如果主标题只是数字（如"主标题1"），则使用副标题作为主标题
                    if main_part.isdigit() or main_part.startswith('主标题'):
                        current_main = sub_part if sub_part else line
                        current_sub = ""
                    else:
                        current_main = main_part
                        current_sub = sub_part
                elif current_main:
                    # 这是副标题的延续
                    current_sub += (' ' + line) if current_sub else line
        
        # 保存最后一个标题
        if current_main:
            title_options.append({"mainTitle": current_main, "subTitle": current_sub.strip()})
        
        # 如果解析失败，使用默认格式
        if not title_options:
            title_options = [
                {"mainTitle": f"{topic} - 深入分析", "subTitle": "探索" + topic + "的最新发展趋势"},
                {"mainTitle": f"{topic}的秘密", "subTitle": "揭开" + topic + "背后的真相"},
                {"mainTitle": f"关于{topic}你需要知道的事", "subTitle": "全面了解" + topic + "的方方面面"}
            ]
        
        print(f"[DEBUG] 解析后的标题选项: {title_options}")
        article_states[task_id]["titleOptions"] = title_options

        await send_sse(task_id, {"type": "AGENT1_COMPLETE"})
        await asyncio.sleep(0.5)
        await send_sse(task_id, {"type": "TITLES_GENERATED", "titleOptions": title_options})

    except Exception as e:
        await send_sse(task_id, {"type": "ERROR", "message": f"生成失败: {str(e)}"})


async def generate_outline(task_id: str):
    """生成大纲"""
    state = article_states.get(task_id)
    if not state:
        return

    topic = state["topic"]
    main_title = state.get("mainTitle", "")
    style = state.get("style", "")
    word_count = state.get("wordCount", 1000)

    try:
        await send_sse(task_id, {"type": "PHASE", "phase": 2, "message": "正在生成大纲..."})

        outline_prompt = f"""你是一个专业的文章大纲设计专家。请根据以下信息生成文章大纲。

主题：{topic}
主标题：{main_title}
风格：{style if style else '通用'}
目标字数：{word_count}字

要求：
1. 生成清晰的文章结构
2. 包含引言、正文各章节、总结
3. 每个章节要有小标题和要点说明
4. 要点要具体、有深度
5. 大纲要逻辑清晰、层次分明

请直接输出大纲，不要有其他说明。"""

        result = await call_ark_api(
            messages=[{"role": "user", "content": outline_prompt}],
            max_tokens=1500
        )

        outline_text = result["choices"][0]["message"]["content"]
        print(f"[DEBUG] AI 返回的大纲文本:\n{outline_text}")
        
        # 解析大纲文本，转换为前端期望的格式
        # 前端期望: Array<{section: number, title: string, points: string[]}>
        outline_options = []
        lines = outline_text.strip().split('\n')
        
        current_section = None
        current_points = []
        
        for line in lines:
            line = line.strip()
            if not line or line == '---':
                continue
            
            # 检测章节标题（## 开头）
            if line.startswith('## '):
                title_text = line[3:].strip()
                # 跳过元数据行（如"主题：xxx"、"风格：xxx"、"目标字数：xxx"）
                if title_text.startswith('主题：') or title_text.startswith('风格：') or title_text.startswith('目标字数：'):
                    continue
                # 保存上一个章节
                if current_section and current_section.strip():
                    outline_options.append({
                        "section": len(outline_options) + 1,
                        "title": current_section.strip(),
                        "points": current_points.copy()
                    })
                # 提取新章节标题
                current_section = title_text
                current_points = []
            elif line.startswith('### '):
                # 小节标题，作为要点处理
                if current_section:
                    current_points.append(line[4:].strip())
            elif line.startswith('#### '):
                # 四级标题（如"要点说明"），跳过
                continue
            elif line.startswith('- ') or line.startswith('* ') or line.startswith('● ') or line.startswith('· '):
                # 列表项要点
                if current_section:
                    point_text = line[2:].strip()
                    if point_text:
                        # 移除"核心要点X："前缀
                        if '核心要点' in point_text:
                            colon_idx = point_text.find('：')
                            if colon_idx > 0:
                                point_text = point_text[colon_idx + 1:].strip()
                        current_points.append(point_text)
            elif line[0].isdigit() and (len(line) == 1 or line[1] == '.' or line[1] == '、'):
                # 数字序号开头的要点（如 "1. xxx" 或 "一、xxx"）
                if current_section:
                    point_text = line[2:].strip() if len(line) > 1 else ''
                    if point_text:
                        # 移除"要点说明"等标记
                        if point_text == '要点说明':
                            continue
                        # 移除"小结："前缀
                        if point_text.startswith('小结：'):
                            point_text = point_text[3:].strip()
                        # 移除"本小节约X字"
                        if '本小节约' in point_text and '字' in point_text:
                            continue
                        current_points.append(point_text)
            elif current_section and line:
                # 其他文本内容作为要点
                # 过滤掉无意义的标记
                if line not in ['要点说明', '小结', '---']:
                    current_points.append(line)
        
        # 保存最后一个章节
        if current_section and current_section.strip():
            outline_options.append({
                "section": len(outline_options) + 1,
                "title": current_section.strip(),
                "points": current_points
            })
        
        # 如果解析失败或没有有效章节，使用默认大纲
        if not outline_options or len(outline_options) == 0:
            outline_options = [
                {"section": 1, "title": "引言", "points": ["介绍主题背景", "提出核心观点"]},
                {"section": 2, "title": "现状分析", "points": ["当前发展状况", "存在的问题"]},
                {"section": 3, "title": "解决方案", "points": ["提出解决方案", "实施步骤"]},
                {"section": 4, "title": "总结展望", "points": ["总结主要观点", "未来发展方向"]}
            ]
        
        # 确保每个章节都有有效的标题和要点
        for i, section in enumerate(outline_options):
            # 确保标题非空
            if not section.get("title") or not section["title"].strip():
                section["title"] = f"章节{i+1}"
            
            # 确保有至少一个要点
            if not section.get("points") or len(section["points"]) == 0:
                section["points"] = ["本章节主要内容"]
            else:
                # 过滤空要点和无意义的要点
                section["points"] = [p for p in section["points"] if p and p.strip() and p not in ['要点说明', '小结']]
                # 如果过滤后没有要点，添加一个默认要点
                if not section["points"]:
                    section["points"] = ["本章节主要内容"]
        
        print(f"[DEBUG] 解析后的大纲: {outline_options}")
        article_states[task_id]["outline"] = outline_options

        print(f"[DEBUG] 发送 AGENT2_COMPLETE 消息")
        await send_sse(task_id, {"type": "AGENT2_COMPLETE"})
        await asyncio.sleep(0.5)
        print(f"[DEBUG] 发送 OUTLINE_GENERATED 消息")
        await send_sse(task_id, {"type": "OUTLINE_GENERATED", "outline": outline_options})
        print(f"[DEBUG] 大纲生成完成")

    except Exception as e:
        await send_sse(task_id, {"type": "ERROR", "message": f"大纲生成失败: {str(e)}"})


async def generate_content(task_id: str):
    """生成正文（流式）"""
    print(f"[DEBUG] 开始生成正文，task_id: {task_id}")
    state = article_states.get(task_id)
    if not state:
        print(f"[DEBUG] 状态不存在，task_id: {task_id}")
        return

    topic = state["topic"]
    main_title = state.get("mainTitle", "")
    sub_title = state.get("subTitle", "")
    outline = state.get("outline", "")
    style = state.get("style", "")
    word_count = state.get("wordCount", 1000)
    print(f"[DEBUG] 主题: {topic}, 标题: {main_title}")

    # 将大纲转换为可读的字符串格式
    outline_str = ""
    if isinstance(outline, list):
        for section in outline:
            title = section.get("title", "")
            points = section.get("points", [])
            outline_str += f"## {title}\n"
            for point in points:
                outline_str += f"- {point}\n"
            outline_str += "\n"
    else:
        outline_str = str(outline)

    try:
        await send_sse(task_id, {"type": "PHASE", "phase": 3, "message": "正在生成正文..."})

        # 字数约束：根据目标字数动态生成更强的约束，避免模型偷懒
        target_wc = int(word_count) if word_count else 1000
        min_wc = int(target_wc * 0.9)
        # 平均每个大纲章节应分配的字数（给模型一个清晰的分配指引）
        section_count = len(outline) if isinstance(outline, list) and outline else 4
        per_section = max(200, target_wc // max(section_count, 1))

        content_prompt = f"""你是一个专业的文章写作专家。请根据以下大纲和要求，生成完整的文章正文。

主题：{topic}
主标题：{main_title}
副标题：{sub_title}
风格：{style if style else '通用'}

【字数硬性要求】
- 目标字数：{target_wc} 字（必须达到，不少于 {min_wc} 字）
- 共 {section_count} 个章节，平均每章节需展开约 {per_section} 字
- 字数不达标视为不合格，请通过举例、引用、案例、数据、对比、延伸思考等方式充分展开

文章大纲：
{outline_str}

要求：
1. 严格按照大纲结构撰写文章，所有章节均需深入展开，不可省略
2. 语言流畅、专业、有深度，避免空话套话
3. 每个章节使用 ## 二级标题，必要的子节点使用 ### 三级标题
4. 多使用具体案例、数据、场景描写，让内容充实有价值
5. 直接输出文章正文，不要在开头/结尾添加说明性文字（如"以下是文章正文"等）
6. 使用 Markdown 格式输出"""

        # 使用流式 API
        api_key = os.getenv("ARK_API_KEY", "")
        base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/coding/v3")
        model = os.getenv("ARK_MODEL", "ark-code-latest")

        print(f"[DEBUG] API Key loaded: {api_key[:8]}...")
        print(f"[DEBUG] Base URL: {base_url}")
        print(f"[DEBUG] Model: {model}")
        print(f"[DEBUG] 提示词长度: {len(content_prompt)}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 根据目标字数动态计算 max_tokens：
        # 中文 1 字约 1.6~2 token，按 2.2x 留冗余；并加 512 给小标题/Markdown 标记的额外开销。
        # 兜底范围 [1024, 16384]，避免无效请求或被服务端拒绝。
        target_word_count = int(word_count) if word_count else 1000
        dynamic_max_tokens = max(1024, min(16384, int(target_word_count * 2.2) + 512))
        print(f"[DEBUG] 目标字数: {target_word_count}, 动态 max_tokens: {dynamic_max_tokens}")

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": content_prompt}],
            "max_tokens": dynamic_max_tokens,
            "stream": True
        }

        full_content = ""
        try:
            # 长文生成可能耗时较久：按 1k 字 ≈ 60s 估算超时，最少 120s，最多 900s
            stream_timeout = max(120.0, min(900.0, target_word_count / 1000 * 60 + 90))
            print(f"[DEBUG] 流式超时: {stream_timeout}s")
            async with httpx.AsyncClient(timeout=stream_timeout) as client:
                print(f"[DEBUG] 调用 API: {base_url}/chat/completions")
                async with client.stream("POST", f"{base_url}/chat/completions", headers=headers, json=payload) as response:
                    print(f"[DEBUG] API Response status: {response.status_code}")
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            if line == "data: [DONE]":
                                break
                            data_str = line[6:]
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        content_chunk = delta["content"]
                                        full_content += content_chunk
                                        print(f"[DEBUG] 收到内容片段，长度: {len(content_chunk)}")
                                        await send_sse(task_id, {"type": "AGENT3_STREAMING", "content": content_chunk})
                            except json.JSONDecodeError:
                                print(f"[DEBUG] JSON解析失败: {data_str[:100]}")
                                continue
            print(f"[DEBUG] 正文生成完成，总长度: {len(full_content)}")
        except Exception as e:
            print(f"[DEBUG] 正文生成API调用失败: {str(e)}")
            raise

        article_states[task_id]["content"] = full_content
        article_states[task_id]["status"] = "COMPLETED"

        await send_sse(task_id, {"type": "AGENT3_COMPLETE"})
        await asyncio.sleep(0.3)
        await send_sse(task_id, {"type": "MERGE_COMPLETE", "fullContent": full_content})
        await asyncio.sleep(0.2)
        await send_sse(task_id, {"type": "ALL_COMPLETE", "content": full_content, "fullContent": full_content})

    except Exception as e:
        await send_sse(task_id, {"type": "ERROR", "message": f"正文生成失败: {str(e)}"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8567, reload=True)
