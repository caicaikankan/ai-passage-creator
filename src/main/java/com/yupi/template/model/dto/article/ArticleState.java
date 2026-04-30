package com.yupi.template.model.dto.article;

import java.util.List;

/**
 * 文章状态
 */
public class ArticleState {

    private String taskId;
    private String topic;
    private String style;
    private TitleInfo title;
    private List<TitleOption> titleOptions;
    private String userDescription;
    private OutlineResult outline;
    private String content;
    private String contentWithPlaceholders;
    private String fullContent;
    private List<ImageRequirement> imageRequirements;
    private List<ImageResult> images;
    private List<String> enabledImageMethods;

    // Getters and Setters
    public String getTaskId() {
        return taskId;
    }

    public void setTaskId(String taskId) {
        this.taskId = taskId;
    }

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

    public TitleInfo getTitle() {
        return title;
    }

    public void setTitle(TitleInfo title) {
        this.title = title;
    }

    public List<TitleOption> getTitleOptions() {
        return titleOptions;
    }

    public void setTitleOptions(List<TitleOption> titleOptions) {
        this.titleOptions = titleOptions;
    }

    public String getUserDescription() {
        return userDescription;
    }

    public void setUserDescription(String userDescription) {
        this.userDescription = userDescription;
    }

    public OutlineResult getOutline() {
        return outline;
    }

    public void setOutline(OutlineResult outline) {
        this.outline = outline;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getContentWithPlaceholders() {
        return contentWithPlaceholders;
    }

    public void setContentWithPlaceholders(String contentWithPlaceholders) {
        this.contentWithPlaceholders = contentWithPlaceholders;
    }

    public String getFullContent() {
        return fullContent;
    }

    public void setFullContent(String fullContent) {
        this.fullContent = fullContent;
    }

    public List<ImageRequirement> getImageRequirements() {
        return imageRequirements;
    }

    public void setImageRequirements(List<ImageRequirement> imageRequirements) {
        this.imageRequirements = imageRequirements;
    }

    public List<ImageResult> getImages() {
        return images;
    }

    public void setImages(List<ImageResult> images) {
        this.images = images;
    }

    public List<String> getEnabledImageMethods() {
        return enabledImageMethods;
    }

    public void setEnabledImageMethods(List<String> enabledImageMethods) {
        this.enabledImageMethods = enabledImageMethods;
    }

    /**
     * 标题信息
     */
    public static class TitleInfo {
        private String mainTitle;
        private String subTitle;

        public TitleInfo() {
        }

        public TitleInfo(String mainTitle, String subTitle) {
            this.mainTitle = mainTitle;
            this.subTitle = subTitle;
        }

        public String getMainTitle() {
            return mainTitle;
        }

        public void setMainTitle(String mainTitle) {
            this.mainTitle = mainTitle;
        }

        public String getSubTitle() {
            return subTitle;
        }

        public void setSubTitle(String subTitle) {
            this.subTitle = subTitle;
        }
    }

    /**
     * 标题选项
     */
    public static class TitleOption {
        private String mainTitle;
        private String subTitle;

        public String getMainTitle() {
            return mainTitle;
        }

        public void setMainTitle(String mainTitle) {
            this.mainTitle = mainTitle;
        }

        public String getSubTitle() {
            return subTitle;
        }

        public void setSubTitle(String subTitle) {
            this.subTitle = subTitle;
        }
    }

    /**
     * 大纲结果
     */
    public static class OutlineResult {
        private List<OutlineSection> sections;

        public List<OutlineSection> getSections() {
            return sections;
        }

        public void setSections(List<OutlineSection> sections) {
            this.sections = sections;
        }

        /**
         * 大纲章节
         */
        public static class OutlineSection {
            private int section;
            private String title;
            private List<String> points;

            public int getSection() {
                return section;
            }

            public void setSection(int section) {
                this.section = section;
            }

            public String getTitle() {
                return title;
            }

            public void setTitle(String title) {
                this.title = title;
            }

            public List<String> getPoints() {
                return points;
            }

            public void setPoints(List<String> points) {
                this.points = points;
            }
        }
    }

    /**
     * 图片需求
     */
    public static class ImageRequirement {
        private String description;
        private String position;

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
        }

        public String getPosition() {
            return position;
        }

        public void setPosition(String position) {
            this.position = position;
        }
    }

    /**
     * 图片结果
     */
    public static class ImageResult {
        private String url;
        private String description;

        public String getUrl() {
            return url;
        }

        public void setUrl(String url) {
            this.url = url;
        }

        public String getDescription() {
            return description;
        }

        public void setDescription(String description) {
            this.description = description;
        }
    }
}
