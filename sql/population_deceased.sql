CREATE TABLE `population_deceased` (
  `id_no` CHAR(18) NOT NULL COMMENT '身份证号码',
  `name` VARCHAR(64) NULL COMMENT '姓名',
  `former_name` VARCHAR(64) NULL COMMENT '曾用名',
  `gender` VARCHAR(16) NULL COMMENT '性别',
  `birth_date` DATE NULL COMMENT '出生年月日',
  `ethnicity` VARCHAR(32) NULL COMMENT '民族',
  `marital_status` VARCHAR(16) NULL COMMENT '婚姻状况',
  `education_level` VARCHAR(32) NULL COMMENT '受教育程度',
  `hukou_province` VARCHAR(32) NULL COMMENT '户籍（省）',
  `hukou_city` VARCHAR(32) NULL COMMENT '户籍（市）',
  `hukou_district` VARCHAR(32) NULL COMMENT '户籍（区）',
  `housing` VARCHAR(64) NULL COMMENT '住房',
  `cur_province` VARCHAR(32) NULL COMMENT '现居住地（省）',
  `cur_city` VARCHAR(32) NULL COMMENT '现居住地（市）',
  `cur_district` VARCHAR(32) NULL COMMENT '现居住地（区）',
  `hukou_type` VARCHAR(32) NULL COMMENT '户籍登记类型',
  `income` DECIMAL(12,2) NULL COMMENT '收入情况（元/月）',
  `processed_at` DATETIME NULL COMMENT '处理时间',
  `source` VARCHAR(64) NULL COMMENT '来源',
  `death_date` DATE NULL COMMENT '死亡年月日',

  PRIMARY KEY (`id_no`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_general_ci
  COMMENT='死亡人口信息';
