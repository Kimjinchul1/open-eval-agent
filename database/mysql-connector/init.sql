-- init.sql - AI Evaluation Database Initial Schema
-- 벤치마크 단위로 테이블 분할

CREATE DATABASE IF NOT EXISTS ai_evaluation;
USE ai_evaluation;

-- 1. AIME Results Table
CREATE TABLE aime_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id VARCHAR(50) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer VARCHAR(10) NOT NULL,
    response TEXT NOT NULL,
    filtered_resps VARCHAR(10),
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') DEFAULT 'Medium',
    business_category VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_difficulty (difficulty),
    INDEX idx_data_id (data_id)
);

-- 2. MMLU Results Table
CREATE TABLE mmlu_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer CHAR(1) NOT NULL,
    choice_a TEXT NOT NULL,
    choice_b TEXT NOT NULL,
    choice_c TEXT NOT NULL,
    choice_d TEXT NOT NULL,
    response TEXT NOT NULL,
    filtered_resps CHAR(1),
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') NOT NULL,
    business_category VARCHAR(50),
    subject VARCHAR(100),
    category ENUM('STEM', 'Humanities', 'Social Science', 'Other'),
    knowledge_source VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_subject (subject),
    INDEX idx_category (category),
    INDEX idx_knowledge_source (knowledge_source)
);

-- 3. DS-MMLU Results Table
CREATE TABLE mmlu_redux_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer CHAR(1) NOT NULL,
    choice_a TEXT NOT NULL,
    choice_b TEXT NOT NULL,
    choice_c TEXT NOT NULL,
    choice_d TEXT NOT NULL,
    response TEXT NOT NULL,
    filtered_resps CHAR(1),
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') NOT NULL,
    business_category VARCHAR(50),
    subject VARCHAR(100),
    category ENUM('STEM', 'Humanities', 'Social Science', 'Other'),
    cultural_context VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_cultural_context (cultural_context)
);

-- 4. MMLU-Pro Results Table
CREATE TABLE mmlu_pro_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer CHAR(1) NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    choice_c TEXT,
    choice_d TEXT,
    response TEXT NOT NULL,
    filtered_resps CHAR(1),
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') NOT NULL,
    business_category VARCHAR(50),
    subject VARCHAR(100),
    category ENUM('STEM', 'Humanities', 'Social Science', 'Other'),
    complexity ENUM('Basic', 'Intermediate', 'Advanced'),
    interdisciplinary VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_interdisciplinary (interdisciplinary),
    INDEX idx_complexity (complexity)
);

-- 5. Math500 Results Table
CREATE TABLE math500_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    choice_c TEXT,
    choice_d TEXT,
    response TEXT NOT NULL,
    filtered_resps TEXT,
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') NOT NULL,
    business_category VARCHAR(50),
    topic VARCHAR(50),
    level VARCHAR(50),
    proof_required BOOLEAN,
    theorem_dependency VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_topic (topic),
    INDEX idx_level (level),
    INDEX idx_proof_required (proof_required)
);

-- 6. DS-MMLU (Semiconductor) Results Table
CREATE TABLE ds_mmlu_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer CHAR(1) NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    choice_c TEXT,
    choice_d TEXT,
    response TEXT NOT NULL,
    filtered_resps CHAR(1),
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') NOT NULL,
    business_category VARCHAR(50),
    subject VARCHAR(100),
    category VARCHAR(50) DEFAULT 'Semiconductor Engineering',
    industry_relevance VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_subject (subject),
    INDEX idx_industry_relevance (industry_relevance)
);

-- 7. HLE (Humanity's Last Exam) Results Table
CREATE TABLE hle_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id VARCHAR(50) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    choice_c TEXT,
    choice_d TEXT,
    choice_e TEXT,
    choice_f TEXT,
    choice_g TEXT,
    choice_h TEXT,
    choice_i TEXT,
    choice_j TEXT,
    response TEXT NOT NULL,
    filtered_resps TEXT,
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') DEFAULT 'Extreme',
    business_category VARCHAR(50),
    category VARCHAR(50),
    complexity VARCHAR(20) DEFAULT 'Ultimate',
    philosophical_domain VARCHAR(50),
    consensus_level VARCHAR(50),
    complexity_breakdown JSON,  -- Dict 메타데이터
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_category (category),
    INDEX idx_philosophical_domain (philosophical_domain),
    INDEX idx_consensus_level (consensus_level)
);

-- 공통 뷰: 전체 성능 요약
CREATE VIEW model_performance_summary AS
SELECT 
    model_name,
    'aime' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM aime_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'mmlu' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM mmlu_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'mmlu-redux' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM mmlu_redux_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'mmlu-pro' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM mmlu_pro_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'math500' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM math500_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'ds-mmlu' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM ds_mmlu_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'hle' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM hle_results GROUP BY model_name;

-- 8. GPQA Results Table
CREATE TABLE gpqa_results (
    id INT PRIMARY KEY AUTO_INCREMENT,
    data_id INT NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    answer CHAR(1) NOT NULL,
    choice_a TEXT,
    choice_b TEXT,
    choice_c TEXT,
    choice_d TEXT,
    response TEXT NOT NULL,
    filtered_resps CHAR(1),
    match_score DECIMAL(3,2) NOT NULL,
    difficulty ENUM('Easy', 'Medium', 'Hard', 'Very Hard', 'Extreme') NOT NULL,
    business_category VARCHAR(50),
    subject VARCHAR(100),
    category VARCHAR(50),
    user_prompt0 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model (model_name),
    INDEX idx_subject (subject),
    INDEX idx_category (category)
);

-- GPQA 벤치마크를 성능 요약 뷰에 추가
DROP VIEW model_performance_summary;
CREATE VIEW model_performance_summary AS
SELECT 
    model_name,
    'aime' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM aime_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'mmlu' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM mmlu_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'mmlu-redux' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM mmlu_redux_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'mmlu-pro' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM mmlu_pro_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'math500' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM math500_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'ds-mmlu' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM ds_mmlu_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'hle' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM hle_results GROUP BY model_name
UNION ALL
SELECT 
    model_name,
    'gpqa' as benchmark,
    COUNT(*) as total_questions,
    AVG(match_score) as avg_score,
    SUM(CASE WHEN match_score = 1.0 THEN 1 ELSE 0 END) as correct_answers
FROM gpqa_results GROUP BY model_name;