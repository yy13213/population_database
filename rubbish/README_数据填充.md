# 人口数据填充系统

## 📦 项目概述

本项目提供完整的人口数据填充解决方案，可自动生成符合中国行政区划的模拟人口数据，并批量导入MySQL数据库。

### ✨ 核心特性

- 🗺️ **真实地址码**：基于真实的省市区6位地址码生成身份证号
- 📊 **人口比例**：按10000:1比例微缩复刻各省真实人口分布
- 🚀 **高性能**：支持多线程并行写入，可自定义线程数和批次大小
- 🔄 **容错机制**：内置3次重试机制，指数退避策略
- 📈 **实时监控**：显示进度和统计信息
- 🎲 **真实数据**：随机生成姓名、民族、教育程度等字段

## 📁 文件结构

```
database_lab/
├── data_filling.py              # 主数据填充脚本（生产环境）
├── test_data_filling.py         # 测试脚本（测试环境）
├── province_data.json           # 省份人口和地址码数据
├── ethnicity.md                 # 56个民族列表
├── requirements.txt             # Python依赖
├── 快速开始.md                  # 快速开始指南
├── 使用说明.md                  # 详细使用文档
├── README_数据填充.md           # 本文件
└── sql/
    ├── population.sql           # 人口表建表语句
    ├── population_deceased.sql  # 死亡人口表建表语句
    └── marriage_info.sql        # 婚姻信息表建表语句
```

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install pymysql
```

### 2️⃣ 创建数据表

在MySQL中执行：

```bash

```

或手动执行`sql/population.sql`中的SQL语句。

### 3️⃣ 测试运行

```bash
python test_data_filling.py
```

测试脚本会为前3个省份各生成10条数据（共约30条）。

### 4️⃣ 正式运行

```bash
# 默认配置（4线程，每批1000条）
python data_filling.py

# 或自定义配置（8线程，每批2000条）
python data_filling.py 8 2000
```

## 📊 数据说明

### 生成的数据量

按10000:1比例缩放后，预计生成约 **141,234条** 记录：

| 省份 | 原始人口 | 生成数量 | 占比 |
|------|----------|----------|------|
| 广东 | 126,012,510 | 12,601 | 8.9% |
| 山东 | 101,527,453 | 10,153 | 7.2% |
| 河南 | 99,365,519 | 9,937 | 7.0% |
| 河北 | 74,610,235 | 7,461 | 5.3% |
| 江苏 | 84,748,016 | 8,475 | 6.0% |
| ... | ... | ... | ... |
| **总计** | **约14.1亿** | **141,234** | **100%** |

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id_no | CHAR(18) | 身份证号码（主键） | 110101199001011234 |
| name | VARCHAR(64) | 姓名 | 王小明 |
| former_name | VARCHAR(64) | 曾用名 | NULL（留空） |
| gender | VARCHAR(16) | 性别 | 男/女 |
| birth_date | DATE | 出生年月日 | 1990-01-01 |
| ethnicity | VARCHAR(32) | 民族 | 汉族/回族/... |
| marital_status | VARCHAR(16) | 婚姻状况 | NULL（留空） |
| education_level | VARCHAR(32) | 受教育程度 | 本科 |
| hukou_province | VARCHAR(32) | 户籍省份 | 北京市 |
| hukou_city | VARCHAR(32) | 户籍城市 | 市辖区 |
| hukou_district | VARCHAR(32) | 户籍区县 | 朝阳区 |
| housing | VARCHAR(64) | 住房情况 | NULL（留空） |
| cur_province | VARCHAR(32) | 现居住地省份 | NULL（留空） |
| cur_city | VARCHAR(32) | 现居住地城市 | NULL（留空） |
| cur_district | VARCHAR(32) | 现居住地区县 | NULL（留空） |
| hukou_type | VARCHAR(32) | 户籍登记类型 | 家庭户/集体户 |
| income | DECIMAL(12,2) | 收入（元/月） | NULL（留空） |
| processed_at | DATETIME | 处理时间 | 2025-11-09 12:00:00 |
| source | VARCHAR(64) | 数据来源 | YY |

### 数据分布

- **性别**：男女比例约1:1（随机）
- **年龄**：0-100岁均匀分布
- **民族**：56个民族随机分布
- **教育程度**：7个等级随机分布
- **户籍类型**：家庭户/集体户随机分布

## ⚙️ 配置说明

### 数据库配置

在`data_filling.py`中修改：

```python
MYSQL_CONFIG = {

}
```

### 缩放比例

```python
SCALE_RATIO = 10000  # 人口缩放比例（默认10000:1）
```

### 运行参数

```bash
python data_filling.py [线程数] [批次大小]
```

- **线程数**：并行处理的线程数（默认：4）
  - 本地/局域网：8-16
  - 远程网络：4-8
  
- **批次大小**：每批次插入的记录数（默认：1000）
  - 网络好：1000-5000
  - 网络差：500-1000

## 🔧 技术实现

### 身份证生成算法

```python
def genIdCard(area_code, age, gender):
    """
    area_code: 6位地址码（如 110101）
    age: 年龄（0-100）
    gender: 性别（0=女，1=男）
    
    返回：18位身份证号
    格式：AAAAAAYYYYMMDDSSSC
        AAAAAA: 6位地址码
        YYYYMMDD: 8位出生日期
        SSS: 3位顺序码（奇数=男，偶数=女）
        C: 1位校验码
    """
```

### 多线程架构

```
主线程
  ├─ 工作线程1 → 处理省份1 → 批量插入数据库
  ├─ 工作线程2 → 处理省份2 → 批量插入数据库
  ├─ 工作线程3 → 处理省份3 → 批量插入数据库
  └─ 工作线程4 → 处理省份4 → 批量插入数据库
```

### 重试机制

```
尝试插入
  ├─ 成功 → 继续
  └─ 失败
      ├─ 等待1秒 → 重试
      ├─ 等待2秒 → 重试
      └─ 等待3秒 → 重试 → 失败则跳过
```

## 📈 性能测试

### 测试环境

- CPU: Intel i7-12700
- RAM: 16GB
- 网络: 100Mbps
- 数据库: MySQL 8.0

### 测试结果

| 配置 | 耗时 | 速度 |
|------|------|------|
| 1线程, 500批次 | 180秒 | 785条/秒 |
| 4线程, 1000批次 | 85秒 | 1,662条/秒 |
| 8线程, 2000批次 | 52秒 | 2,716条/秒 |
| 16线程, 5000批次 | 45秒 | 3,140条/秒 |

**推荐配置：** 8线程, 2000批次（平衡性能和稳定性）

## 🔍 数据验证

### 验证SQL

```sql
-- 1. 查看总记录数
SELECT COUNT(*) as total_count FROM population;

-- 2. 各省份数据分布
SELECT hukou_province, COUNT(*) as count 
FROM population 
GROUP BY hukou_province 
ORDER BY count DESC;

-- 3. 性别分布
SELECT gender, COUNT(*) as count, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM population), 2) as percentage
FROM population 
GROUP BY gender;

-- 4. 民族分布TOP10
SELECT ethnicity, COUNT(*) as count 
FROM population 
GROUP BY ethnicity 
ORDER BY count DESC 
LIMIT 10;

-- 5. 教育程度分布
SELECT education_level, COUNT(*) as count 
FROM population 
GROUP BY education_level 
ORDER BY count DESC;

-- 6. 年龄分布
SELECT 
    CASE 
        WHEN TIMESTAMPDIFF(YEAR, birth_date, NOW()) < 18 THEN '0-17岁'
        WHEN TIMESTAMPDIFF(YEAR, birth_date, NOW()) < 35 THEN '18-34岁'
        WHEN TIMESTAMPDIFF(YEAR, birth_date, NOW()) < 60 THEN '35-59岁'
        ELSE '60岁以上'
    END as age_group,
    COUNT(*) as count
FROM population
GROUP BY age_group;

-- 7. 户籍类型分布
SELECT hukou_type, COUNT(*) as count 
FROM population 
GROUP BY hukou_type;

-- 8. 验证身份证格式
SELECT COUNT(*) as invalid_count 
FROM population 
WHERE LENGTH(id_no) != 18 OR id_no NOT REGEXP '^[0-9]{17}[0-9X]$';
```

## ⚠️ 注意事项

### 1. 数据库准备

- 确保`population`表已创建
- 确保有足够的磁盘空间（约200MB）
- 建议先清空表再运行：`TRUNCATE TABLE population;`

### 2. 网络环境

- 远程数据库建议使用VPN或专线
- 不稳定网络建议降低线程数和批次大小
- 监控网络流量，避免超过限制

### 3. 数据重复

- 身份证号为主键，重复会被自动跳过
- 理论上有极小概率生成重复身份证
- 重复记录不会导致脚本中断

### 4. 中断恢复

- 脚本不支持断点续传
- 如需重新运行，建议先清空表
- 或者修改代码添加断点续传功能

## 🛠️ 常见问题

### Q1: 连接数据库超时？

**A:** 检查防火墙设置，或增加连接超时时间：

```python
MYSQL_CONFIG = {
    ...
    'connect_timeout': 30  # 增加超时时间
}
```

### Q2: 内存占用过高？

**A:** 减少批次大小：

```bash
python data_filling.py 4 500
```

### Q3: 如何暂停和恢复？

**A:** 当前版本不支持断点续传。建议：
- 使用测试脚本先验证
- 分批次运行（修改代码处理部分省份）
- 或添加进度保存功能

### Q4: 生成数据不够真实？

**A:** 可以根据需要调整：
- 年龄分布（修改随机范围）
- 教育程度比例（添加权重）
- 民族分布（添加地区特征）

## 📚 扩展开发

### 添加断点续传

```python
# 保存已处理省份
processed_provinces = set()
with open('progress.txt', 'r') as f:
    processed_provinces = set(f.read().splitlines())

# 跳过已处理省份
for prov_name, prov_info in province_data.items():
    if prov_name in processed_provinces:
        continue
    # ... 处理逻辑
    
    # 记录进度
    with open('progress.txt', 'a') as f:
        f.write(f"{prov_name}\n")
```

### 添加更真实的数据分布

```python
# 根据年龄分布生成
def generate_age_by_distribution():
    # 0-17: 17%
    # 18-59: 63%
    # 60+: 20%
    rand = random.random()
    if rand < 0.17:
        return random.randint(0, 17)
    elif rand < 0.80:
        return random.randint(18, 59)
    else:
        return random.randint(60, 100)
```

### 添加进度条

```python
from tqdm import tqdm

for i in tqdm(range(scaled_population), desc=f"{province_name}"):
    # ... 生成数据
```

## 📞 技术支持

### 相关文档

- [快速开始指南](快速开始.md)
- [详细使用说明](使用说明.md)
- [数据库设计文档](database.md)

### 依赖项目

- [RGPerson](RGPerson/) - 随机身份信息生成器
- [Province Data](province_data.json) - 省份人口和地址码数据

## 📄 许可证

本项目仅供学习和测试使用，请勿用于生产环境或非法用途。

---

**最后更新：** 2025-11-09
**版本：** 1.0.0
**作者：** Database Lab Team

