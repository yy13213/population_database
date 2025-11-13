-- ============================================================
-- 内存数据库表创建脚本
-- 使用 MEMORY 引擎提升查询性能
-- ============================================================

USE population;

-- ============================================================
-- 设置内存表大小限制（根据数据量调整）
-- ============================================================
-- 全局设置（需要 SUPER 权限）
SET GLOBAL max_heap_table_size = 10737418240;  -- 10GB
SET GLOBAL tmp_table_size = 10737418240;       -- 10GB

-- 当前会话设置
SET SESSION max_heap_table_size = 10737418240; -- 10GB
SET SESSION tmp_table_size = 10737418240;      -- 10GB

-- ============================================================
-- 1. 人口基础信息表（内存版）
-- ============================================================
DROP TABLE IF EXISTS population_memory;

CREATE TABLE population_memory (
    id_no CHAR(18) NOT NULL COMMENT '身份证号码',
    name VARCHAR(64) DEFAULT NULL COMMENT '姓名',
    former_name VARCHAR(64) DEFAULT NULL COMMENT '曾用名',
    gender VARCHAR(16) DEFAULT NULL COMMENT '性别',
    birth_date DATE DEFAULT NULL COMMENT '出生日期',
    ethnicity VARCHAR(32) DEFAULT NULL COMMENT '民族',
    marital_status VARCHAR(16) DEFAULT NULL COMMENT '婚姻状况',
    education_level VARCHAR(32) DEFAULT NULL COMMENT '受教育程度',
    hukou_province VARCHAR(32) DEFAULT NULL COMMENT '户籍省份',
    hukou_city VARCHAR(32) DEFAULT NULL COMMENT '户籍城市',
    hukou_district VARCHAR(32) DEFAULT NULL COMMENT '户籍区县',
    housing VARCHAR(64) DEFAULT NULL COMMENT '住房情况',
    cur_province VARCHAR(32) DEFAULT NULL COMMENT '现居住省份',
    cur_city VARCHAR(32) DEFAULT NULL COMMENT '现居住城市',
    cur_district VARCHAR(32) DEFAULT NULL COMMENT '现居住区县',
    hukou_type VARCHAR(32) DEFAULT NULL COMMENT '户籍类型',
    income DECIMAL(12,2) DEFAULT NULL COMMENT '收入',
    processed_at DATETIME DEFAULT NULL COMMENT '处理时间',
    source VARCHAR(64) DEFAULT NULL COMMENT '数据来源',
    id_card_photo VARCHAR(255) DEFAULT NULL COMMENT '身份证照片路径',
    
    PRIMARY KEY (id_no),
    INDEX idx_hukou_province (hukou_province),
    INDEX idx_cur_province (cur_province),
    INDEX idx_gender (gender),
    INDEX idx_birth_date (birth_date),
    INDEX idx_ethnicity (ethnicity)
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb4 COMMENT='人口信息内存表';

-- ============================================================
-- 2. 死亡人口信息表（内存版）
-- ============================================================
DROP TABLE IF EXISTS population_deceased_memory;

CREATE TABLE population_deceased_memory (
    id_no CHAR(18) NOT NULL COMMENT '身份证号码',
    name VARCHAR(64) DEFAULT NULL COMMENT '姓名',
    former_name VARCHAR(64) DEFAULT NULL COMMENT '曾用名',
    gender VARCHAR(16) DEFAULT NULL COMMENT '性别',
    birth_date DATE DEFAULT NULL COMMENT '出生日期',
    ethnicity VARCHAR(32) DEFAULT NULL COMMENT '民族',
    marital_status VARCHAR(16) DEFAULT NULL COMMENT '婚姻状况',
    education_level VARCHAR(32) DEFAULT NULL COMMENT '受教育程度',
    hukou_province VARCHAR(32) DEFAULT NULL COMMENT '户籍省份',
    hukou_city VARCHAR(32) DEFAULT NULL COMMENT '户籍城市',
    hukou_district VARCHAR(32) DEFAULT NULL COMMENT '户籍区县',
    housing VARCHAR(64) DEFAULT NULL COMMENT '住房情况',
    cur_province VARCHAR(32) DEFAULT NULL COMMENT '现居住省份',
    cur_city VARCHAR(32) DEFAULT NULL COMMENT '现居住城市',
    cur_district VARCHAR(32) DEFAULT NULL COMMENT '现居住区县',
    hukou_type VARCHAR(32) DEFAULT NULL COMMENT '户籍类型',
    income DECIMAL(12,2) DEFAULT NULL COMMENT '收入',
    processed_at DATETIME DEFAULT NULL COMMENT '处理时间',
    source VARCHAR(64) DEFAULT NULL COMMENT '数据来源',
    death_date DATE DEFAULT NULL COMMENT '死亡日期',
    
    PRIMARY KEY (id_no),
    INDEX idx_death_date (death_date),
    INDEX idx_hukou_province (hukou_province)
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb4 COMMENT='死亡人口信息内存表';

-- ============================================================
-- 3. 婚姻登记信息表（内存版）
-- ============================================================
DROP TABLE IF EXISTS marriage_info_memory;

CREATE TABLE marriage_info_memory (
    male_name VARCHAR(64) DEFAULT NULL COMMENT '男方姓名',
    female_name VARCHAR(64) DEFAULT NULL COMMENT '女方姓名',
    male_id_no CHAR(18) NOT NULL COMMENT '男方身份证号',
    female_id_no CHAR(18) NOT NULL COMMENT '女方身份证号',
    marriage_date DATE DEFAULT NULL COMMENT '结婚日期',
    
    PRIMARY KEY (male_id_no, female_id_no),
    INDEX idx_male_id (male_id_no),
    INDEX idx_female_id (female_id_no),
    INDEX idx_marriage_date (marriage_date)
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb4 COMMENT='婚姻信息内存表';

-- ============================================================
-- 4. 同步元数据表（InnoDB 引擎，持久化）
-- ============================================================
DROP TABLE IF EXISTS memory_sync_metadata;

CREATE TABLE memory_sync_metadata (
    table_name VARCHAR(64) NOT NULL PRIMARY KEY COMMENT '表名',
    last_sync_time DATETIME NOT NULL COMMENT '上次同步时间',
    record_count BIGINT NOT NULL DEFAULT 0 COMMENT '记录数',
    sync_duration_seconds DECIMAL(10,2) DEFAULT NULL COMMENT '同步耗时（秒）',
    sync_status VARCHAR(32) DEFAULT 'success' COMMENT '同步状态',
    error_message TEXT DEFAULT NULL COMMENT '错误信息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='内存表同步元数据';

-- ============================================================
-- 5. 初始化同步元数据
-- ============================================================
INSERT INTO memory_sync_metadata (table_name, last_sync_time, record_count) VALUES
('population_memory', NOW(), 0),
('population_deceased_memory', NOW(), 0),
('marriage_info_memory', NOW(), 0)
ON DUPLICATE KEY UPDATE last_sync_time = NOW();

-- ============================================================
-- 查看内存表信息
-- ============================================================
SELECT 
    table_name AS '表名',
    engine AS '存储引擎',
    table_rows AS '行数',
    ROUND(data_length / 1024 / 1024, 2) AS '数据大小(MB)',
    ROUND(index_length / 1024 / 1024, 2) AS '索引大小(MB)'
FROM information_schema.tables
WHERE table_schema = 'population' 
AND table_name LIKE '%_memory'
ORDER BY table_name;

-- ============================================================
-- 完成提示
-- ============================================================
SELECT '✅ 内存表创建完成！' AS 'Status',
       '下一步：运行 sync_to_memory.py 同步数据' AS 'Next Step';

