-- ============================================================
-- 山东省数据视图创建脚本
-- 创建3个视图：人口、婚姻、死亡数据
-- ============================================================

USE population;

-- ============================================================
-- 1. 山东省人口数据视图
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
WHERE hukou_province = '山东省'
   OR cur_province = '山东省';

-- ============================================================
-- 2. 山东省死亡人口数据视图
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
WHERE hukou_province = '山东省'
   OR cur_province = '山东省';

-- ============================================================
-- 3. 山东省婚姻数据视图
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
    AND (p.hukou_province = '山东省' OR p.cur_province = '山东省')
);

-- ============================================================
-- 验证视图创建
-- ============================================================
SELECT '✅ 视图创建完成！' AS 'Status';

-- 显示视图信息
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

-- 查看视图列表
SHOW FULL TABLES WHERE table_type = 'VIEW';

SHOW FULL PROCESSLIST;-- 杀死那个查询 shandong_population 的进程


-- 杀死那些查询 shandong_marriage 的进程
-- (你不需要全部杀死，先杀死几个最老的，锁就会释放)
KILL 20090;
KILL 20094;
KILL 20102;
KILL 20103;
KILL 20103;

SELECT COUNT(*) FROM shandong_marriage
SELECT COUNT(*) FROM shandong_marriage
