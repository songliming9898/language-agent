-- ============================================
-- 小学生英语口语对练 Agent - 数据库初始化脚本
-- ============================================

CREATE DATABASE IF NOT EXISTS kids_english
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE kids_english;

-- 1. 课程主表
CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grade VARCHAR(20) NOT NULL COMMENT '年级，如 Grade3',
    semester VARCHAR(20) NOT NULL COMMENT '学期，如 上/下',
    version VARCHAR(50) DEFAULT '2024' COMMENT '教材版本',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) COMMENT '课程主表';

-- 2. 课程单元表
CREATE TABLE IF NOT EXISTS course_units (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    unit_name VARCHAR(100) NOT NULL COMMENT '单元名称',
    unit_order INT NOT NULL COMMENT '单元序号',
    description TEXT COMMENT '单元描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) COMMENT '课程单元';

-- 3. 句子/对话表
CREATE TABLE IF NOT EXISTS sentences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit_id INT NOT NULL,
    sentence_text TEXT NOT NULL COMMENT '英文句子',
    sentence_order INT NOT NULL COMMENT '排序',
    audio_url VARCHAR(500) DEFAULT NULL COMMENT '标准发音音频URL',
    translation VARCHAR(500) DEFAULT NULL COMMENT '中文翻译',
    difficulty ENUM('easy','medium','hard') DEFAULT 'easy',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES course_units(id) ON DELETE CASCADE
) COMMENT '课程句子';

-- 4. 对话历史表
CREATE TABLE IF NOT EXISTS conversations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL DEFAULT 1 COMMENT '用户ID，Demo固定为1',
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    mode ENUM('course','free_talk') NOT NULL COMMENT '对练模式',
    course_unit_id INT DEFAULT NULL COMMENT '关联课程单元',
    role ENUM('user','assistant','system') NOT NULL,
    message_text TEXT NOT NULL,
    audio_url VARCHAR(500) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (user_id, session_id, created_at)
) COMMENT '对话记录';

-- 5. 用户学习进度表
CREATE TABLE IF NOT EXISTS user_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL DEFAULT 1,
    sentence_id INT NOT NULL,
    practice_count INT DEFAULT 0 COMMENT '练习次数',
    score_accuracy FLOAT DEFAULT 0 COMMENT '音准分',
    score_fluency FLOAT DEFAULT 0 COMMENT '流利度分',
    score_completeness FLOAT DEFAULT 0 COMMENT '完整度分',
    last_practice_at TIMESTAMP NULL,
    mastered BOOLEAN DEFAULT FALSE COMMENT '是否掌握',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sentence_id) REFERENCES sentences(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_sentence (user_id, sentence_id)
) COMMENT '用户学习进度';

-- 6. 用户记忆表
CREATE TABLE IF NOT EXISTS memory_records (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL DEFAULT 1,
    memory_type ENUM(
        'vocab_mastered',
        'vocab_weak',
        'grammar_weak',
        'pronunciation_issue',
        'learning_preference',
        'interest_topic'
    ) NOT NULL COMMENT '记忆类型',
    `key` VARCHAR(200) NOT NULL COMMENT '记忆关键词',
    `value` TEXT COMMENT '记忆内容',
    confidence FLOAT DEFAULT 0.5 COMMENT '置信度 0-1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_type (user_id, memory_type),
    UNIQUE KEY uk_user_key (user_id, memory_type, `key`)
) COMMENT '用户记忆';

-- ============================================
-- 插入三年级教材基础数据（骨架）
-- ============================================

-- 三年级上册
INSERT INTO courses (grade, semester, version) VALUES ('Grade3', '上册', 'PEP-2024');

-- 三年级下册
INSERT INTO courses (grade, semester, version) VALUES ('Grade3', '下册', 'PEP-2024');

-- 上册单元
INSERT INTO course_units (course_id, unit_name, unit_order, description) VALUES
(1, 'Unit 1 Hello!', 1, '打招呼与自我介绍'),
(1, 'Unit 2 Colours', 2, '颜色认知'),
(1, 'Unit 3 Look at Me!', 3, '身体部位'),
(1, 'Unit 4 We Love Animals', 4, '动物名称'),
(1, 'Unit 5 Let''s Eat!', 5, '食物与点餐'),
(1, 'Unit 6 Happy Birthday!', 6, '数字与生日祝福');

-- 下册单元
INSERT INTO course_units (course_id, unit_name, unit_order, description) VALUES
(2, 'Unit 1 Welcome Back to School!', 1, '返校问候'),
(2, 'Unit 2 My Family', 2, '家庭成员'),
(2, 'Unit 3 At the Zoo', 3, '动物园动物描述'),
(2, 'Unit 4 Where Is My Car?', 4, '方位介词'),
(2, 'Unit 5 Do You Like Pears?', 5, '水果与喜好'),
(2, 'Unit 6 How Many?', 6, '数量问答');
