package com.yupi.template.model.dto.article;

import java.util.List;

/**
 * 文章创建请求
 */
public class ArticleCreateRequest {

    private String topic;
    private String style;
    private List<String> enabledImageMethods;

    public String getTopic() {
        return topic;
    }

    public void setTopic(String topic) {
        this.topic = topic;
    }

    public String getStyle() {
        return style;
    }

    public void setStyle(String style) {
        this.style = style;
    }

    public List<String> getEnabledImageMethods() {
        return enabledImageMethods;
    }

    public void setEnabledImageMethods(List<String> enabledImageMethods) {
        this.enabledImageMethods = enabledImageMethods;
    }
}
