package com.yupi.template.model.enums;

/**
 * SSE 消息类型枚举
 */
public enum SseMessageTypeEnum {

    AGENT1_COMPLETE("AGENT1_COMPLETE", "标题方案生成完成"),
    AGENT2_STREAMING("AGENT2_STREAMING", "大纲流式输出中"),
    AGENT2_COMPLETE("AGENT2_COMPLETE", "大纲生成完成"),
    AGENT3_STREAMING("AGENT3_STREAMING", "正文流式输出中"),
    AGENT3_COMPLETE("AGENT3_COMPLETE", "正文生成完成"),
    AGENT4_COMPLETE("AGENT4_COMPLETE", "配图需求分析完成"),
    IMAGE_COMPLETE("IMAGE_COMPLETE", "单张配图生成完成"),
    AGENT5_COMPLETE("AGENT5_COMPLETE", "所有配图生成完成"),
    MERGE_COMPLETE("MERGE_COMPLETE", "图文合成完成"),
    ERROR("ERROR", "错误通知");

    private final String value;
    private final String description;

    SseMessageTypeEnum(String value, String description) {
        this.value = value;
        this.description = description;
    }

    public String getValue() {
        return value;
    }

    public String getDescription() {
        return description;
    }
}
