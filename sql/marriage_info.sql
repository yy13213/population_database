CREATE TABLE marriage_info (
  male_name VARCHAR(64) NULL COMMENT '姓名（男）',
  female_name VARCHAR(64) NULL COMMENT '姓名（女）',
  male_id_no CHAR(18) NOT NULL COMMENT '身份证号码（男）',
  female_id_no CHAR(18) NOT NULL COMMENT '身份证号码（女）',
  marriage_date DATE NULL COMMENT '结婚时间',
  PRIMARY KEY (male_id_no, female_id_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='结婚情况表';