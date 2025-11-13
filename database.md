# 📘 人口信息数据库 README

## 一、数据库概述

本数据库用于存储人口基础信息、死亡人口信息及婚姻登记信息，支持人口数据的统计、查询、更新及关联分析。
系统包含以下三张核心表：

* `population`：人口基础信息表
* `population_deceased`：死亡人口信息表
* `marriage_info`：结婚情况表

---

## 二、表结构说明

### 1️⃣ `population` — 人口基础信息表

**用途**：存储常住人口的基本资料，包括身份、教育、婚姻、收入等信息。

| 字段名                                                | 类型            | 说明              |
| -------------------------------------------------- | ------------- | --------------- |
| `id_no`                                            | CHAR(18)      | 身份证号码，主键，唯一标识个人 |
| `name`                                             | VARCHAR(64)   | 姓名              |
| `former_name`                                      | VARCHAR(64)   | 曾用名             |
| `gender`                                           | VARCHAR(16)   | 性别              |
| `birth_date`                                       | DATE          | 出生年月日           |
| `ethnicity`                                        | VARCHAR(32)   | 民族              |
| `marital_status`                                   | VARCHAR(16)   | 婚姻状况            |
| `education_level`                                  | VARCHAR(32)   | 受教育程度           |
| `hukou_province` / `hukou_city` / `hukou_district` | VARCHAR(32)   | 户籍所在地（省、市、区）    |
| `housing`                                          | VARCHAR(64)   | 住房情况            |
| `cur_province` / `cur_city` / `cur_district`       | VARCHAR(32)   | 现居住地（省、市、区）     |
| `hukou_type`                                       | VARCHAR(32)   | 户籍登记类型          |
| `income`                                           | DECIMAL(12,2) | 收入情况（元/月）       |
| `processed_at`                                     | DATETIME      | 处理时间            |
| `source`                                           | VARCHAR(64)   | 数据来源            |

**主键**：`id_no`

---

### 2️⃣ `population_deceased` — 死亡人口信息表

**用途**：记录死亡人口的信息，字段结构与 `population` 基本一致，额外包含死亡日期。

| 字段名            | 类型   | 说明    |
| -------------- | ---- | ----- |
| （同 population） |      | 同上    |
| `death_date`   | DATE | 死亡年月日 |

**主键**：`id_no`
**说明**：
可通过 `id_no` 与 `population` 表进行关联，用于统计死亡率或分析人口变动。

---

### 3️⃣ `marriage_info` — 结婚情况表

**用途**：记录婚姻登记信息，包括男女双方姓名、身份证号码及结婚时间。

| 字段名             | 类型          | 说明      |
| --------------- | ----------- | ------- |
| `male_name`     | VARCHAR(64) | 男方姓名    |
| `female_name`   | VARCHAR(64) | 女方姓名    |
| `male_id_no`    | CHAR(18)    | 男方身份证号码 |
| `female_id_no`  | CHAR(18)    | 女方身份证号码 |
| `marriage_date` | DATE        | 结婚时间    |

**主键**：`(male_id_no, female_id_no)`（联合主键）
**说明**：

* 确保同一对配偶仅出现一次；
* 可与 `population` 表联合查询个人婚姻状况、配偶信息等。

---

## 三、表之间的关系

| 表名                                   | 关联方式           | 说明                   |
| ------------------------------------ | -------------- | -------------------- |
| `population` ↔ `population_deceased` | 一对一（按 `id_no`） | 同一身份证号对应的生/死状态       |
| `population` ↔ `marriage_info`       | 一对多            | 一个人可出现在多个婚姻记录中（历史婚姻） |

---

## 四、设计说明

* **字符集**：`utf8mb4`（支持中文与特殊字符）
* **引擎**：`InnoDB`（支持事务与外键）
* **时间字段**建议存储为本地时区统一格式（如 `DATETIME`）
* **数据来源字段 (`source`)** 可追踪导入渠道（如公安系统、民政局、用户录入等）

---

## 五、扩展建议

* 在 `population` 表中增加唯一性约束或触发器，防止身份证号重复；
* 可根据业务需求添加外键约束，例如：

  ```sql
  ALTER TABLE marriage_info
  ADD FOREIGN KEY (male_id_no) REFERENCES population(id_no),
  ADD FOREIGN KEY (female_id_no) REFERENCES population(id_no);
  ```


MYSQL_CONFIG = {

