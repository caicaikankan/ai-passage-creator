package com.yupi.template.controller;

import com.yupi.template.agent.ArticleAgentOrchestrator;
import com.yupi.template.model.dto.article.ArticleCreateRequest;
import com.yupi.template.model.dto.article.ArticleState;
import com.yupi.template.model.enums.SseMessageTypeEnum;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import jakarta.annotation.Resource;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 文章控制器
 */
@RestController
@RequestMapping("/article")
@Slf4j
public class ArticleController {

    @Resource
    private ArticleAgentOrchestrator articleAgentOrchestrator;

    // 存储 SSE 连接
    private static final Map<String, SseEmitter> SSE_EMITTERS = new ConcurrentHashMap<>();

    /**
     * 创建文章
     */
    @PostMapping("/create")
    public String createArticle(@RequestBody ArticleCreateRequest request) {
        String taskId = UUID.randomUUID().toString();
        log.info("创建文章任务: taskId={}, topic={}", taskId, request.getTopic());
        
        // 创建文章状态
        ArticleState state = new ArticleState();
        state.setTaskId(taskId);
        state.setTopic(request.getTopic());
        state.setStyle(request.getStyle());
        state.setEnabledImageMethods(request.getEnabledImageMethods());
        
        // 生成标题
        new Thread(() -> {
            try {
                articleAgentOrchestrator.executePhase1_GenerateTitles(state, message -> {
                    sendSSEMessage(taskId, message);
                });
            } catch (Exception e) {
                log.error("标题生成失败: taskId={}", taskId, e);
                sendSSEMessage(taskId, SseMessageTypeEnum.ERROR.getValue());
            }
        }).start();
        
        return taskId;
    }

    /**
     * 确认标题
     */
    @PostMapping("/confirm-title")
    public void confirmTitle(@RequestBody Map<String, Object> request) {
        String taskId = (String) request.get("taskId");
        String mainTitle = (String) request.get("selectedMainTitle");
        String subTitle = (String) request.get("selectedSubTitle");
        String userDescription = (String) request.get("userDescription");

        log.info("确认标题: taskId={}, mainTitle={}", taskId, mainTitle);

        // 创建文章状态
        ArticleState state = new ArticleState();
        state.setTaskId(taskId);
        state.setTitle(new ArticleState.TitleInfo(mainTitle, subTitle));
        state.setUserDescription(userDescription);

        // 生成大纲
        new Thread(() -> {
            try {
                articleAgentOrchestrator.executePhase2_GenerateOutline(state, message -> {
                    sendSSEMessage(taskId, message);
                });
            } catch (Exception e) {
                log.error("大纲生成失败: taskId={}", taskId, e);
                sendSSEMessage(taskId, SseMessageTypeEnum.ERROR.getValue());
            }
        }).start();
    }

    /**
     * 确认大纲
     */
    @PostMapping("/confirm-outline")
    public void confirmOutline(@RequestBody Map<String, Object> request) {
        String taskId = (String) request.get("taskId");
        log.info("确认大纲: taskId={}", taskId);

        // 创建文章状态
        ArticleState state = new ArticleState();
        state.setTaskId(taskId);

        // 生成正文和配图
        new Thread(() -> {
            try {
                articleAgentOrchestrator.executePhase3_GenerateContent(state, message -> {
                    sendSSEMessage(taskId, message);
                });
            } catch (Exception e) {
                log.error("正文+配图生成失败: taskId={}", taskId, e);
                sendSSEMessage(taskId, SseMessageTypeEnum.ERROR.getValue());
            }
        }).start();
    }

    /**
     * SSE 连接
     */
    @GetMapping("/progress/{taskId}")
    public SseEmitter progress(@PathVariable String taskId) {
        SseEmitter emitter = new SseEmitter(3600_000L);
        SSE_EMITTERS.put(taskId, emitter);

        emitter.onCompletion(() -> {
            SSE_EMITTERS.remove(taskId);
            log.info("SSE 连接完成: taskId={}", taskId);
        });

        emitter.onTimeout(() -> {
            SSE_EMITTERS.remove(taskId);
            log.info("SSE 连接超时: taskId={}", taskId);
        });

        log.info("建立 SSE 连接: taskId={}", taskId);
        return emitter;
    }

    /**
     * 发送 SSE 消息
     */
    private void sendSSEMessage(String taskId, String message) {
        SseEmitter emitter = SSE_EMITTERS.get(taskId);
        if (emitter != null) {
            try {
                emitter.send(message);
            } catch (Exception e) {
                log.error("发送 SSE 消息失败: taskId={}", taskId, e);
                SSE_EMITTERS.remove(taskId);
            }
        }
    }
}
