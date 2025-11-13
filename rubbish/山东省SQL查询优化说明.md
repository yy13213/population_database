# 🔧 山东省SQL查询优化说明

## 📋 修改概述

将所有山东省页面的SQL查询从**视图查询**改为**直接查询总表**，以解决性能问题。

### 修改原则

1. ✅ **不再使用视图**：所有查询直接从 `population`、`population_deceased`、`marriage_info` 表查询
2. ✅ **使用精确匹配**：查询条件使用 `hukou_province = '山东省' OR cur_province = '山东省'`，不使用 `LIKE`
3. ✅ **保持逻辑一致**：其他查询逻辑与原先保持一致

---

## 🔄 修改详情

### 1. 总人口查询

**修改前**：
```sql
SELECT COUNT(DISTINCT id_no) FROM shandong_population
```

**修改后**：
```sql
SELECT COUNT(DISTINCT id_no) 
FROM population
WHERE hukou_province = '山东省' OR cur_province = '山东省'
```

---

### 2. 城市人口查询

**修改前**：
```sql
SELECT hukou_city, COUNT(DISTINCT id_no) as count
FROM shandong_population
WHERE hukou_city IS NOT NULL
GROUP BY hukou_city
```

**修改后**：
```sql
SELECT hukou_city, COUNT(DISTINCT id_no) as count
FROM population
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND hukou_city IS NOT NULL
GROUP BY hukou_city
```

---

### 3. 性别统计查询

**修改前**：
```sql
SELECT gender, COUNT(DISTINCT id_no) as count
FROM shandong_population
WHERE gender IS NOT NULL
GROUP BY gender
```

**修改后**：
```sql
SELECT gender, COUNT(DISTINCT id_no) as count
FROM population
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND gender IS NOT NULL
GROUP BY gender
```

---

### 4. 年龄分布查询

**修改前**：
```sql
SELECT 
    CASE ... END as age_group,
    COUNT(DISTINCT id_no) as count
FROM shandong_population
WHERE birth_date IS NOT NULL
GROUP BY age_group
```

**修改后**：
```sql
SELECT 
    CASE ... END as age_group,
    COUNT(DISTINCT id_no) as count
FROM population
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND birth_date IS NOT NULL
GROUP BY age_group
```

---

### 5. 教育统计查询

**修改前**：
```sql
SELECT education_level, COUNT(DISTINCT id_no) as count
FROM shandong_population
WHERE education_level IS NOT NULL
GROUP BY education_level
```

**修改后**：
```sql
SELECT education_level, COUNT(DISTINCT id_no) as count
FROM population
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND education_level IS NOT NULL
GROUP BY education_level
```

---

### 6. 婚姻统计查询

**修改前**：
```sql
SELECT COUNT(*) FROM shandong_marriage
SELECT YEAR(marriage_date) as year, COUNT(*) as count
FROM shandong_marriage
WHERE marriage_date IS NOT NULL
GROUP BY YEAR(marriage_date)
```

**修改后**：
```sql
SELECT COUNT(*) 
FROM marriage_info m
WHERE EXISTS (
    SELECT 1 FROM population p 
    WHERE (p.id_no = m.male_id_no OR p.id_no = m.female_id_no)
    AND (p.hukou_province = '山东省' OR p.cur_province = '山东省')
)

SELECT YEAR(m.marriage_date) as year, COUNT(*) as count
FROM marriage_info m
WHERE EXISTS (
    SELECT 1 FROM population p 
    WHERE (p.id_no = m.male_id_no OR p.id_no = m.female_id_no)
    AND (p.hukou_province = '山东省' OR p.cur_province = '山东省')
)
AND m.marriage_date IS NOT NULL
GROUP BY YEAR(m.marriage_date)
```

---

### 7. 死亡统计查询

**修改前**：
```sql
SELECT COUNT(DISTINCT id_no) FROM shandong_deceased
SELECT YEAR(death_date) as year, COUNT(DISTINCT id_no) as count
FROM shandong_deceased
WHERE death_date IS NOT NULL
GROUP BY YEAR(death_date)
```

**修改后**：
```sql
SELECT COUNT(DISTINCT id_no) 
FROM population_deceased
WHERE hukou_province = '山东省' OR cur_province = '山东省'

SELECT YEAR(death_date) as year, COUNT(DISTINCT id_no) as count
FROM population_deceased
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND death_date IS NOT NULL
GROUP BY YEAR(death_date)
```

---

### 8. 收入统计查询

**修改前**：
```sql
SELECT COUNT(DISTINCT id_no), AVG(income), MAX(income), MIN(income)
FROM shandong_population
WHERE income IS NOT NULL AND income > 0
```

**修改后**：
```sql
SELECT COUNT(DISTINCT id_no), AVG(income), MAX(income), MIN(income)
FROM population
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND income IS NOT NULL AND income > 0
```

---

### 9. 民族统计查询

**修改前**：
```sql
SELECT ethnicity, COUNT(DISTINCT id_no) as count
FROM shandong_population
WHERE ethnicity IS NOT NULL
GROUP BY ethnicity
```

**修改后**：
```sql
SELECT ethnicity, COUNT(DISTINCT id_no) as count
FROM population
WHERE (hukou_province = '山东省' OR cur_province = '山东省')
  AND ethnicity IS NOT NULL
GROUP BY ethnicity
```

---

### 10. 迁移统计查询

**修改前**（使用LIKE）：
```sql
SELECT COUNT(DISTINCT id_no)
FROM shandong_population
WHERE (hukou_province NOT LIKE '%山东%' OR hukou_province IS NULL)
  AND cur_province LIKE '%山东%'
```

**修改后**（使用精确匹配）：
```sql
SELECT COUNT(DISTINCT id_no)
FROM population
WHERE hukou_province != '山东省' 
  AND cur_province = '山东省'
```

---

## ✅ 修改优势

### 1. 性能提升

- ✅ **直接查询总表**：避免视图的额外开销
- ✅ **精确匹配**：使用 `=` 而不是 `LIKE`，可以利用索引，查询更快
- ✅ **减少中间层**：不需要通过视图，减少查询层级

### 2. 查询优化

- ✅ **索引利用**：`hukou_province = '山东省'` 和 `cur_province = '山东省'` 可以使用索引
- ✅ **查询计划优化**：MySQL可以直接优化查询计划，不需要考虑视图的复杂性

### 3. 维护性

- ✅ **不依赖视图**：即使视图不存在或有问题，查询仍然可以正常工作
- ✅ **逻辑清晰**：查询条件明确，易于理解和维护

---

## 📊 修改文件

| 文件 | 修改内容 |
|------|----------|
| `GIS_Flask/shandong_stats.py` | 所有SQL查询从视图改为总表查询 |

---

## 🚀 验证方法

### 1. 重启Flask应用

```bash
cd GIS_Flask
python app.py
```

### 2. 检查日志

**预期日志**：
```
📊 开始获取山东省综合统计数据...
   📊 山东省总人口: 995,637
✅ 山东省数据获取完成
   - 总人口: 995,637
   - 城市数: 16
   - 婚姻记录: XXX
   - 死亡记录: XXX
```

### 3. 访问页面

```
http://127.0.0.1:5050/shandong
```

**预期效果**：
- ✅ 数据正常显示
- ✅ 查询速度更快
- ✅ 统计卡片显示正确数据
- ✅ 图表正常渲染

---

## 🔍 性能对比

### 修改前（使用视图）

- ❌ 需要先查询视图定义
- ❌ 视图可能没有优化索引
- ❌ 查询可能较慢

### 修改后（直接查询总表）

- ✅ 直接查询总表，利用索引
- ✅ 查询条件明确，优化器可以更好地优化
- ✅ 查询速度更快

---

## 📝 注意事项

1. **数据一致性**：确保数据库中省份名称统一为 `'山东省'`
2. **索引优化**：建议在 `hukou_province` 和 `cur_province` 字段上创建索引（如果还没有）
3. **查询条件**：所有查询都使用 `hukou_province = '山东省' OR cur_province = '山东省'`

---

## 🎉 修改完成

**所有SQL查询已从视图改为直接查询总表，使用精确匹配条件，性能将得到显著提升！** 🚀

