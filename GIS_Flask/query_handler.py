#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能查询处理模块
支持手动SQL查询和自然语言查询
"""
import pymysql
import json
import time
from openai import OpenAI
from typing import Dict, List, Any, Tuple

# 数据库配置
MYSQL_CONFIG = {

}

# DeepSeek API 配置
API_KEY = "sk-09a288c0cec54a5c8cbc68cefd3333b7"
BASE_URL = "https://api.deepseek.com"


class QueryHandler:
    """查询处理类"""
    
    def __init__(self):
        self.connection = None
        self.ai_client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    def connect_db(self) -> bool:
        """连接数据库"""
        try:
            if self.connection and self.connection.open:
                return True
            self.connection = pymysql.connect(**MYSQL_CONFIG)
            return True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return False
    
    def close_db(self):
        """关闭数据库连接"""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
    
    def execute_sql(self, sql: str, use_memory_tables: bool = True) -> Tuple[bool, Any, float, str]:
        """
        执行SQL查询
        :param sql: SQL语句
        :param use_memory_tables: 是否使用内存表
        :return: (成功标志, 结果, 执行时间, 错误信息)
        """
        if not self.connect_db():
            return False, None, 0, "数据库连接失败"
        
        cursor = self.connection.cursor()
        
        try:
            # 如果使用内存表，替换表名
            if use_memory_tables:
                sql = sql.replace('population_deceased', 'population_deceased_memory')
                sql = sql.replace('marriage_info', 'marriage_info_memory')
                sql = sql.replace('population', 'population_memory')
            
            # 执行查询
            start_time = time.time()
            cursor.execute(sql)
            duration = time.time() - start_time
            
            # 获取结果
            if sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                
                # 获取列名
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # 转换为字典列表
                data = []
                for row in results:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # 处理特殊类型
                        if value is None:
                            row_dict[col] = None
                        elif isinstance(value, (int, float, str, bool)):
                            row_dict[col] = value
                        else:
                            row_dict[col] = str(value)
                    data.append(row_dict)
                
                return True, {'columns': columns, 'data': data, 'count': len(data)}, duration, ""
            else:
                # 非查询语句（INSERT, UPDATE, DELETE等）
                self.connection.commit()
                affected_rows = cursor.rowcount
                return True, {'affected_rows': affected_rows}, duration, ""
        
        except Exception as e:
            error_msg = str(e)
            return False, None, 0, error_msg
        
        finally:
            cursor.close()
    
    def generate_sql_from_nl(self, question: str) -> Tuple[bool, str, str]:
        """
        从自然语言生成SQL
        :param question: 用户问题
        :return: (成功标志, SQL语句, 错误信息)
        """
        try:
            # 数据库schema信息
            schema_info = """
数据库名称: population

表1: population_memory (人口信息表)
字段:
- id_no (CHAR(18)): 身份证号码，主键
- name (VARCHAR(64)): 姓名
- former_name (VARCHAR(64)): 曾用名
- gender (VARCHAR(16)): 性别（男/女）
- birth_date (DATE): 出生日期
- ethnicity (VARCHAR(32)): 民族
- marital_status (VARCHAR(16)): 婚姻状况
- education_level (VARCHAR(32)): 受教育程度
- hukou_province (VARCHAR(32)): 户籍省份
- hukou_city (VARCHAR(32)): 户籍城市
- hukou_district (VARCHAR(32)): 户籍区县
- housing (VARCHAR(64)): 住房情况
- cur_province (VARCHAR(32)): 现居住省份
- cur_city (VARCHAR(32)): 现居住城市
- cur_district (VARCHAR(32)): 现居住区县
- hukou_type (VARCHAR(32)): 户籍类型
- income (DECIMAL(12,2)): 收入（元/月）
- processed_at (DATETIME): 处理时间
- source (VARCHAR(64)): 数据来源

表2: population_deceased_memory (死亡人口信息表)
字段: 与population_memory相同，额外增加:
- death_date (DATE): 死亡日期

表3: marriage_info_memory (婚姻信息表)
字段:
- male_name (VARCHAR(64)): 男方姓名
- female_name (VARCHAR(64)): 女方姓名
- male_id_no (CHAR(18)): 男方身份证号，主键之一
- female_id_no (CHAR(18)): 女方身份证号，主键之一
- marriage_date (DATE): 结婚日期

注意事项:
1. 使用内存表（_memory后缀）
2. 省份名称已简化（如"广东"而非"广东省"）
3. 性别只有"男"和"女"两个值
4. 日期格式: YYYY-MM-DD
5. 查询人口迁移: hukou_province != cur_province
"""

            # 构建提示词
            prompt = f"""你是一个SQL专家。根据用户的问题和数据库schema，生成准确的SQL查询语句。

{schema_info}

用户问题: {question}

要求:
1. 只返回SQL语句，不要有任何其他说明
2. SQL语句必须是有效的MySQL语法
3. 使用内存表（表名带_memory后缀）
4. 对于统计查询，使用GROUP BY和聚合函数
5. 限制结果数量时使用LIMIT，建议不超过1000条
6. 对于复杂查询，可以使用子查询或JOIN

返回格式要求:
请以JSON格式返回，包含以下字段:
{{
    "sql": "生成的SQL语句",
    "explanation": "简短的SQL说明（中文）",
    "estimated_rows": 预估返回行数（数字）
}}

只返回JSON，不要有其他内容。"""

            # 调用DeepSeek API
            response = self.ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的SQL专家，擅长根据自然语言生成SQL查询。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # 解析响应
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            try:
                # 去除可能的markdown代码块标记
                if content.startswith('```'):
                    content = content.split('```')[1]
                    if content.startswith('json'):
                        content = content[4:]
                    content = content.strip()
                
                result = json.loads(content)
                sql = result.get('sql', '').strip()
                
                if not sql:
                    return False, "", "AI未能生成有效的SQL"
                
                return True, sql, ""
            
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试直接提取SQL
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'SHOW', 'DESCRIBE')):
                        return True, line, ""
                
                return False, "", f"无法解析AI响应: {content}"
        
        except Exception as e:
            return False, "", f"AI调用失败: {str(e)}"
    
    def generate_answer_from_results(self, question: str, sql: str, results: Dict) -> str:
        """
        根据查询结果生成自然语言答案
        :param question: 用户问题
        :param sql: 执行的SQL
        :param results: 查询结果
        :return: 自然语言答案
        """
        try:
            # 构建提示词
            result_summary = f"查询返回了 {results.get('count', 0)} 条记录"
            
            if results.get('count', 0) > 0:
                # 限制显示的数据量
                data_preview = results['data'][:10]  # 最多显示10条
                result_summary += f"\n\n数据示例:\n{json.dumps(data_preview, ensure_ascii=False, indent=2)}"
            
            prompt = f"""用户问题: {question}

执行的SQL: {sql}

查询结果: {result_summary}

请根据查询结果，用简洁清晰的中文回答用户的问题。要求:
1. 直接回答问题，不要重复问题
2. 如果有数字统计，突出显示关键数据
3. 如果结果为空，说明没有找到相关数据
4. 保持专业和友好的语气
5. 如果结果很多，总结关键信息

回答:"""

            # 调用AI生成答案
            response = self.ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个友好的数据分析助手，擅长解释查询结果。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            return answer
        
        except Exception as e:
            return f"生成答案失败: {str(e)}"
    
    def process_nl_query(self, question: str, use_memory_tables: bool = True) -> Dict:
        """
        处理自然语言查询的完整流程
        :param question: 用户问题
        :param use_memory_tables: 是否使用内存表
        :return: 完整结果字典
        """
        result = {
            'success': False,
            'question': question,
            'sql': '',
            'sql_generation_time': 0,
            'sql_execution_time': 0,
            'query_results': None,
            'answer': '',
            'error': ''
        }
        
        try:
            # 1. 生成SQL
            start_time = time.time()
            success, sql, error = self.generate_sql_from_nl(question)
            result['sql_generation_time'] = time.time() - start_time
            
            if not success:
                result['error'] = f"SQL生成失败: {error}"
                return result
            
            result['sql'] = sql
            
            # 2. 执行SQL
            success, query_results, exec_time, error = self.execute_sql(sql, use_memory_tables)
            result['sql_execution_time'] = exec_time
            
            if not success:
                result['error'] = f"SQL执行失败: {error}"
                return result
            
            result['query_results'] = query_results
            
            # 3. 生成答案
            if query_results:
                answer = self.generate_answer_from_results(question, sql, query_results)
                result['answer'] = answer
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = f"处理失败: {str(e)}"
        
        finally:
            self.close_db()
        
        return result


# 测试代码
if __name__ == '__main__':
    handler = QueryHandler()
    
    # 测试手动SQL
    print("=" * 60)
    print("测试手动SQL查询")
    print("=" * 60)
    success, results, duration, error = handler.execute_sql(
        "SELECT hukou_province, COUNT(*) as count FROM population_memory GROUP BY hukou_province LIMIT 5"
    )
    print(f"成功: {success}")
    print(f"耗时: {duration:.3f}秒")
    if success:
        print(f"结果: {json.dumps(results, ensure_ascii=False, indent=2)}")
    else:
        print(f"错误: {error}")
    
    # 测试自然语言查询
    print("\n" + "=" * 60)
    print("测试自然语言查询")
    print("=" * 60)
    result = handler.process_nl_query("查询广东省有多少人口？")
    print(json.dumps(result, ensure_ascii=False, indent=2))

