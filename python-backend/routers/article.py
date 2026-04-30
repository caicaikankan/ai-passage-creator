"""文章路由"""

import asyncio
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(tags=["文章管理"])

# 内存存储文章状态
article_states = {}

# 存储 SSE 连接
sse_connections = {}

@router.post("/create")
async def create_article(
    request: Request,
):
    """创建文章任务"""
    data = await request.json()
    topic = data.get("topic")
    style = data.get("style")
    enabled_image_methods = data.get("enabledImageMethods", [])
    word_count = data.get("wordCount", 1000)  # 默认1000字
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    # 存储文章状态
    article_states[task_id] = {
        "topic": topic,
        "style": style,
        "enabled_image_methods": enabled_image_methods,
        "wordCount": word_count
    }
    
    # 模拟标题生成
    asyncio.create_task(simulate_title_generation(task_id))
    
    return {"code": 0, "data": task_id, "message": "任务创建成功"}

@router.post("/confirm-title")
async def confirm_title(
    request: Request,
):
    """确认标题"""
    data = await request.json()
    task_id = data.get("taskId")
    selected_main_title = data.get("selectedMainTitle")
    selected_sub_title = data.get("selectedSubTitle")
    user_description = data.get("userDescription")
    
    # 存储标题信息
    if task_id in article_states:
        article_states[task_id].update({
            "mainTitle": selected_main_title,
            "subTitle": selected_sub_title,
            "userDescription": user_description
        })
        
        # 模拟大纲生成
        asyncio.create_task(simulate_outline_generation(task_id))
    
    return {"code": 0, "data": None, "message": "标题确认成功"}

@router.post("/confirm-outline")
async def confirm_outline(
    request: Request,
):
    """确认大纲"""
    data = await request.json()
    task_id = data.get("taskId")
    
    # 模拟正文和配图生成
    asyncio.create_task(simulate_content_generation(task_id))
    
    return {"code": 0, "data": None, "message": "大纲确认成功"}

@router.post("/list")
async def list_articles(
    request: Request,
):
    """分页查询文章列表"""
    data = await request.json()
    page_num = data.get("pageNum", 1)
    page_size = data.get("pageSize", 10)
    
    # 转换为文章列表
    articles = []
    for task_id, state in article_states.items():
        articles.append({
            "taskId": task_id,
            "topic": state.get("topic", ""),
            "mainTitle": state.get("mainTitle", ""),
            "subTitle": state.get("subTitle", ""),
            "createTime": "2024-01-01 00:00:00",
            "status": "COMPLETED"
        })
    
    # 分页处理
    start = (page_num - 1) * page_size
    end = start + page_size
    paginated_articles = articles[start:end]
    
    return {
        "code": 0,
        "data": {
            "records": paginated_articles,
            "total": len(articles),
            "pageNum": page_num,
            "pageSize": page_size
        },
        "message": "success"
    }

@router.get("/progress/{task_id}")
async def progress(
    task_id: str,
):
    """SSE 连接"""
    async def event_generator():
        # 存储连接
        sse_connections[task_id] = asyncio.Queue()
        
        try:
            while True:
                # 从队列获取消息
                message = await sse_connections[task_id].get()
                # 发送SSE消息
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            # 连接关闭
            if task_id in sse_connections:
                del sse_connections[task_id]
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

async def simulate_title_generation(task_id: str):
    """模拟标题生成"""
    await asyncio.sleep(2)
    
    # 获取选题
    topic = article_states.get(task_id, {}).get("topic", "学习效率")
    
    # 根据选题生成标题选项
    title_options = [
        {
            "mainTitle": f"如何提高{topic}效率", 
            "subTitle": "5个实用技巧让你事半功倍"
        },
        {
            "mainTitle": f"高效{topic}的秘诀", 
            "subTitle": "从心理学角度解析学习方法"
        },
        {
            "mainTitle": f"{topic}效率提升指南", 
            "subTitle": "科学方法助你快速掌握知识"
        }
    ]
    
    # 存储标题选项
    if task_id in article_states:
        article_states[task_id]["titleOptions"] = title_options
    
    # 发送SSE消息
    await send_sse_message(task_id, {"type": "AGENT1_COMPLETE"})
    await asyncio.sleep(1)
    await send_sse_message(task_id, {"type": "TITLES_GENERATED", "titleOptions": title_options})

async def simulate_outline_generation(task_id: str):
    """模拟大纲生成"""
    await asyncio.sleep(3)
    
    # 获取选题
    topic = article_states.get(task_id, {}).get("topic", "学习效率")
    
    # 模拟大纲
    outline = [
        {
            "section": 1, 
            "title": "引言", 
            "points": [
                f"{topic}的重要性",
                f"当前{topic}中的常见问题"
            ]
        },
        {
            "section": 2, 
            "title": f"提高{topic}效率的方法", 
            "points": [
                "时间管理技巧",
                "专注力提升",
                "记忆方法优化"
            ]
        },
        {
            "section": 3, 
            "title": "实践案例", 
            "points": [
                "成功学习者的经验",
                "如何将方法应用到日常"
            ]
        },
        {
            "section": 4, 
            "title": "总结", 
            "points": [
                "关键要点回顾",
                "持续改进的重要性"
            ]
        }
    ]
    
    # 存储大纲
    if task_id in article_states:
        article_states[task_id]["outline"] = outline
    
    # 发送SSE消息
    await send_sse_message(task_id, {"type": "AGENT2_COMPLETE"})
    await asyncio.sleep(1)
    await send_sse_message(task_id, {"type": "OUTLINE_GENERATED", "outline": outline})

async def simulate_content_generation(task_id: str):
    """模拟正文和配图生成"""
    await asyncio.sleep(4)
    
    # 获取选题和标题
    topic = article_states.get(task_id, {}).get("topic", "学习效率")
    main_title = article_states.get(task_id, {}).get("mainTitle", f"如何提高{topic}效率")
    sub_title = article_states.get(task_id, {}).get("subTitle", "5个实用技巧让你事半功倍")
    word_count = article_states.get(task_id, {}).get("wordCount", 1000)
    
    # 根据字数生成不同长度的文章
    full_content = generate_content_by_length(topic, main_title, sub_title, word_count)
    
    # 发送SSE消息
    await send_sse_message(task_id, {"type": "AGENT3_COMPLETE"})
    await asyncio.sleep(1)
    await send_sse_message(task_id, {"type": "AGENT4_COMPLETE", "imageRequirements": [
        {"type": "diagram", "description": "番茄工作法流程图"},
        {"type": "chart", "description": "艾森豪威尔矩阵"},
        {"type": "icon", "description": "专注力图标"},
        {"type": "graph", "description": "艾宾浩斯遗忘曲线"},
        {"type": "photo", "description": "学习场景图片"}
    ]})
    await asyncio.sleep(1)
    await send_sse_message(task_id, {"type": "AGENT5_COMPLETE", "images": [
        {"type": "diagram", "url": "https://via.placeholder.com/400x300?text=番茄工作法"},
        {"type": "chart", "url": "https://via.placeholder.com/400x300?text=艾森豪威尔矩阵"},
        {"type": "icon", "url": "https://via.placeholder.com/400x300?text=专注力"},
        {"type": "graph", "url": "https://via.placeholder.com/400x300?text=遗忘曲线"},
        {"type": "photo", "url": "https://via.placeholder.com/400x300?text=学习场景"}
    ]})
    await asyncio.sleep(1)
    await send_sse_message(task_id, {"type": "MERGE_COMPLETE", "fullContent": full_content})
    await asyncio.sleep(1)
    await send_sse_message(task_id, {"type": "ALL_COMPLETE"})

def generate_content_by_length(topic: str, main_title: str, sub_title: str, word_count: int) -> str:
    """根据字数生成不同长度的文章（四档：1000，2000，5000，8000+）"""
    
    # 短篇（约1000字）
    short_content = f"""# {main_title}

## {sub_title}

### 引言

在当今快节奏的社会中，{topic}效率已经成为每个人都需要掌握的核心技能。无论是学生、职场人士还是终身学习者，提高{topic}效率都能让我们在有限的时间内获得更多的知识和技能。

### 一、时间管理技巧

#### 番茄工作法

番茄工作法是一种简单有效的时间管理方法。具体步骤如下：选择一个{topic}任务，设置25分钟的专注时间，专注{topic}不做其他事情，休息5分钟，重复4个周期后休息15-30分钟。这种方法能够帮助我们保持专注，避免长时间{topic}导致的疲劳。

#### 优先级管理

使用艾森豪威尔矩阵将任务分为四类：重要且紧急、重要但不紧急、不重要但紧急、不重要且不紧急。通过合理分配时间，我们可以更高效地完成{topic}任务。

### 二、专注力提升

{topic}环境对专注力有重要影响。建议关闭手机通知，整理{topic}空间，使用白噪音或轻音乐，设置固定的{topic}时间。主动{topic}比被动接收更有效，包括提问式{topic}、思考式{topic}和实践式{topic}。

### 三、总结

提高{topic}效率不是一蹴而就的，需要持续的努力和实践。找到适合自己的方法并坚持下去，你一定能够成为高效的{topic}者！
"""
    
    # 中篇（约2000字）
    medium_content = f"""# {main_title}

## {sub_title}

### 引言

在当今快节奏的社会中，{topic}效率已经成为每个人都需要掌握的核心技能。无论是学生、职场人士还是终身学习者，提高{topic}效率都能让我们在有限的时间内获得更多的知识和技能。

然而，很多人在{topic}过程中常常遇到各种问题：注意力不集中、记忆效果差、学习进度缓慢等。这些问题不仅浪费时间，还会打击我们的自信心和积极性。

### 一、时间管理技巧

#### 1.1 番茄工作法

番茄工作法是一种简单有效的时间管理方法。具体步骤如下：选择一个{topic}任务，设置25分钟的专注时间，专注{topic}不做其他事情，休息5分钟，重复4个周期后休息15-30分钟。这种方法能够帮助我们保持专注，避免长时间{topic}导致的疲劳。

#### 1.2 优先级管理

使用艾森豪威尔矩阵将任务分为四类：重要且紧急立即处理，重要但不紧急安排时间处理，不重要但紧急委托他人或快速处理，不重要且不紧急删除或推迟。

### 二、专注力提升

#### 2.1 消除干扰

{topic}环境对专注力有重要影响。建议关闭手机通知，整理{topic}空间，使用白噪音或轻音乐，设置固定的{topic}时间。

#### 2.2 主动{topic}

主动{topic}比被动接收更有效：提问式{topic}、思考式{topic}、实践式{topic}。

### 三、记忆方法优化

艾宾浩斯遗忘曲线告诉我们，遗忘是有规律的。通过间隔重复可以有效对抗遗忘：第1次复习在{topic}后立即进行，第2次在1天后，第3次在3天后，第4次在7天后，第5次在15天后。

### 四、总结

提高{topic}效率不是一蹴而就的，需要持续的努力和实践。尝试不同的技巧，找到最适合自己的组合，坚持下去！
"""
    
    # 长篇（约5000字）
    long_content = f"""# {main_title}

## {sub_title}

### 引言

在当今快节奏的社会中，{topic}效率已经成为每个人都需要掌握的核心技能。无论是学生、职场人士还是终身学习者，提高{topic}效率都能让我们在有限的时间内获得更多的知识和技能。

然而，很多人在{topic}过程中常常遇到各种问题：注意力不集中、记忆效果差、学习进度缓慢等。这些问题不仅浪费时间，还会打击我们的自信心和积极性。本文将深入探讨提高{topic}效率的方法和技巧。

### 一、时间管理技巧

#### 1.1 番茄工作法

番茄工作法是一种简单有效的时间管理方法。具体步骤如下：选择一个{topic}任务，设置25分钟的专注时间，专注{topic}不做其他事情，休息5分钟，重复4个周期后休息15-30分钟。

#### 1.2 优先级管理

使用艾森豪威尔矩阵将任务分为四类：重要且紧急立即处理，重要但不紧急安排时间处理，不重要但紧急委托他人或快速处理，不重要且不紧急删除或推迟。

#### 1.3 时间块管理

将一天划分为多个时间块，每个时间块专注于一项任务。这种方法可以帮助我们更好地规划时间，提高{topic}效率。

### 二、专注力提升

#### 2.1 消除干扰

{topic}环境对专注力有重要影响。建议关闭手机通知，整理{topic}空间，使用白噪音或轻音乐，设置固定的{topic}时间。

#### 2.2 主动{topic}

主动{topic}比被动接收更有效：提问式{topic}、思考式{topic}、实践式{topic}。

#### 2.3 深度工作

深度工作是指在无干扰的状态下专注进行职业活动，使个人的认知能力达到极限。通过深度工作，我们可以更快地掌握新知识和技能。

### 三、记忆方法优化

#### 3.1 间隔重复

艾宾浩斯遗忘曲线告诉我们，遗忘是有规律的。通过间隔重复可以有效对抗遗忘。

#### 3.2 联想记忆法

将新知识与已有知识建立联系：比喻法、故事法、图像法。

#### 3.3 思维导图

使用思维导图可以帮助我们更好地组织和记忆知识。通过可视化的方式，我们可以更清晰地理解知识之间的关系。

### 四、实践案例

#### 4.1 成功学习者的经验

许多成功的学习者都运用了这些方法：比尔·盖茨每年阅读50本书并做笔记，沃伦·巴菲特每天花80%的时间阅读和思考，埃隆·马斯克通过第一性原理学习新领域。

#### 4.2 如何应用到日常

将这些方法应用到日常{topic}中：制定计划，记录进度，定期回顾，持续改进。

### 五、常见问题与解决方案

在{topic}过程中，我们可能会遇到各种问题。以下是一些常见问题及其解决方案：

- **注意力不集中**：尝试使用番茄工作法，设置专注时间。
- **记忆效果差**：运用间隔重复和联想记忆法。
- **学习进度缓慢**：检查学习方法是否适合自己，尝试调整策略。

### 六、总结

提高{topic}效率需要综合运用多种方法。时间管理、专注力提升、记忆方法优化等都是提高{topic}效率的关键。尝试不同的技巧，找到最适合自己的组合，坚持下去，你一定能够成为高效的{topic}者！
"""
    
    # 超长篇（8000字+）
    max_content = f"""# {main_title}

## {sub_title}

### 引言

在当今快节奏的社会中，{topic}效率已经成为每个人都需要掌握的核心技能。无论是学生、职场人士还是终身学习者，提高{topic}效率都能让我们在有限的时间内获得更多的知识和技能。

然而，很多人在{topic}过程中常常遇到各种问题：注意力不集中、记忆效果差、学习进度缓慢等。这些问题不仅浪费时间，还会打击我们的自信心和积极性。本文将全面深入地探讨提高{topic}效率的方法和技巧，帮助你成为高效的{topic}者。

### 一、时间管理技巧

#### 1.1 番茄工作法

番茄工作法是一种简单有效的时间管理方法。具体步骤如下：选择一个{topic}任务，设置25分钟的专注时间，专注{topic}不做其他事情，休息5分钟，重复4个周期后休息15-30分钟。

#### 1.2 优先级管理

使用艾森豪威尔矩阵将任务分为四类：重要且紧急立即处理，重要但不紧急安排时间处理，不重要但紧急委托他人或快速处理，不重要且不紧急删除或推迟。

#### 1.3 时间块管理

将一天划分为多个时间块，每个时间块专注于一项任务。这种方法可以帮助我们更好地规划时间，提高{topic}效率。

#### 1.4 GTD时间管理

GTD（Getting Things Done）是一种高效的时间管理方法，包括收集、整理、组织、回顾和执行五个步骤。

### 二、专注力提升

#### 2.1 消除干扰

{topic}环境对专注力有重要影响。建议关闭手机通知，整理{topic}空间，使用白噪音或轻音乐，设置固定的{topic}时间。

#### 2.2 主动{topic}

主动{topic}比被动接收更有效：提问式{topic}、思考式{topic}、实践式{topic}。

#### 2.3 深度工作

深度工作是指在无干扰的状态下专注进行职业活动，使个人的认知能力达到极限。

#### 2.4 心流状态

心流是一种完全沉浸在活动中的状态，此时注意力高度集中，时间感消失。通过进入心流状态，我们可以极大地提高{topic}效率。

### 三、记忆方法优化

#### 3.1 间隔重复

艾宾浩斯遗忘曲线告诉我们，遗忘是有规律的。通过间隔重复可以有效对抗遗忘。

#### 3.2 联想记忆法

将新知识与已有知识建立联系：比喻法、故事法、图像法。

#### 3.3 思维导图

使用思维导图可以帮助我们更好地组织和记忆知识。

#### 3.4 费曼学习法

费曼学习法是一种高效的学习方法，包括学习、讲授、纠错和简化四个步骤。

### 四、实践案例

#### 4.1 成功学习者的经验

许多成功的学习者都运用了这些方法：比尔·盖茨每年阅读50本书并做笔记，沃伦·巴菲特每天花80%的时间阅读和思考，埃隆·马斯克通过第一性原理学习新领域。

#### 4.2 如何应用到日常

将这些方法应用到日常{topic}中：制定计划，记录进度，定期回顾，持续改进。

### 五、常见问题与解决方案

在{topic}过程中，我们可能会遇到各种问题。以下是一些常见问题及其解决方案：

- **注意力不集中**：尝试使用番茄工作法，设置专注时间。
- **记忆效果差**：运用间隔重复和联想记忆法。
- **学习进度缓慢**：检查学习方法是否适合自己，尝试调整策略。
- **缺乏动力**：设定明确的目标，建立奖励机制。

### 六、工具推荐

以下是一些有助于提高{topic}效率的工具：

- **时间管理工具**：番茄钟应用、待办事项清单工具
- **笔记工具**：Notion、Obsidian、Evernote
- **专注工具**：Forest、Focus@Will
- **记忆工具**：Anki、Quizlet

### 七、心态调整

良好的心态对于提高{topic}效率至关重要。保持好奇心、接受失败、保持耐心，这些都是成功{topic}者的共同特质。

### 八、总结

提高{topic}效率需要综合运用多种方法。时间管理、专注力提升、记忆方法优化等都是提高{topic}效率的关键。尝试不同的技巧，找到最适合自己的组合，坚持下去，你一定能够成为高效的{topic}者！

---

**温馨提示**：{topic}是一个终身的过程，保持好奇心和求知心，享受{topic}的乐趣，你会发现{topic}变得更加轻松和高效！
"""
    
    # 根据字数选择内容（四档：1000，2000，5000，8000+）
    if word_count <= 1000:
        return short_content
    elif word_count <= 2000:
        return medium_content
    elif word_count <= 5000:
        return long_content
    else:
        return max_content


async def send_sse_message(task_id: str, message: dict):
    """发送SSE消息"""
    import json
    if task_id in sse_connections:
        # 将消息发送到队列
        await sse_connections[task_id].put(json.dumps(message))
