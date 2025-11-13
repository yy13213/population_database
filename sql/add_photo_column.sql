-- 在population表中添加身份证照片存储路径字段
-- 执行此SQL来添加新列

USE population;

-- 添加新列
ALTER TABLE population 
ADD COLUMN id_card_photo VARCHAR(255) DEFAULT NULL COMMENT '身份证照片存储路径';

-- 查看表结构（验证）
DESCRIBE population;

-- 查看现有数据（所有照片路径应为NULL）
SELECT id_no, name, id_card_photo FROM population LIMIT 10;

