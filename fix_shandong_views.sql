-- ============================================================
-- 山东省视图快速修复脚本
-- 使用 LIKE '%山东%' 匹配所有包含"山东"的省份名称
-- ============================================================

USE population;

-- ============================================================
-- 1. 重新创建山东省人口数据视图
-- ============================================================
DROP VIEW IF EXISTS shandong_population;

CREATE VIEW shandong_population AS
SELECT 
    id_no,
    name,
    former_name,
    gender,
    birth_date,
    ethnicity,
    marital_status,
    education_level,
    hukou_province,
    hukou_city,
    hukou_district,
    housing,
    cur_province,
    cur_city,
    cur_district,
    hukou_type,
    income,
    processed_at,
    source,
    id_card_photo
FROM population
WHERE hukou_province LIKE '%山东%'
   OR cur_province LIKE '%山东%';

-- ============================================================
-- 2. 重新创建山东省死亡人口数据视图
-- ============================================================
DROP VIEW IF EXISTS shandong_deceased;

CREATE VIEW shandong_deceased AS
SELECT 
    id_no,
    name,
    former_name,
    gender,
    birth_date,
    ethnicity,
    marital_status,
    education_level,
    hukou_province,
    hukou_city,
    hukou_district,
    housing,
    cur_province,
    cur_city,
    cur_district,
    hukou_type,
    income,
    processed_at,
    source,
    death_date
FROM population_deceased
WHERE hukou_province LIKE '%山东%'
   OR cur_province LIKE '%山东%';

-- ============================================================
-- 3. 重新创建山东省婚姻数据视图
-- ============================================================
DROP VIEW IF EXISTS shandong_marriage;

CREATE VIEW shandong_marriage AS
SELECT 
    m.male_name,
    m.female_name,
    m.male_id_no,
    m.female_id_no,
    m.marriage_date
FROM marriage_info m
WHERE EXISTS (
    SELECT 1 FROM population p 
    WHERE (p.id_no = m.male_id_no OR p.id_no = m.female_id_no)
    AND (p.hukou_province LIKE '%山东%' OR p.cur_province LIKE '%山东%')
);

-- ============================================================
-- 验证视图
-- ============================================================
SELECT '✅ 视图修复完成！' AS 'Status';

-- 显示视图数据量
SELECT 
    '山东省人口视图' AS '视图名称',
    COUNT(*) AS '记录数'
FROM shandong_population
UNION ALL
SELECT 
    '山东省死亡人口视图',
    COUNT(*)
FROM shandong_deceased
UNION ALL
SELECT 
    '山东省婚姻视图',
    COUNT(*)
FROM shandong_marriage;

-- 检查原始表中的数据
SELECT 
    '原始表-户籍' AS '数据源',
    hukou_province AS '省份名称',
    COUNT(DISTINCT id_no) AS '记录数'
FROM population
WHERE hukou_province LIKE '%山东%'
GROUP BY hukou_province
UNION ALL
SELECT 
    '原始表-现居',
    cur_province,
    COUNT(DISTINCT id_no)
FROM population
WHERE cur_province LIKE '%山东%'
GROUP BY cur_province;

