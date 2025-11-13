"""
批量修复所有查询方法，替换 cursor.execute 为 execute_query
"""

def update_method(method_name, query_part):
    """生成更新后的方法代码"""
    return f'''    def {method_name}(self) -> Dict[str, Dict]:
        """原始方法"""
        query = """{query_part}"""
        
        try:
            results = self.execute_query(query)
            # 处理结果
            return process_results(results)
        except Exception as e:
            print(f"❌ {method_name} 失败: {{e}}")
            return {{}}
'''

# 需要更新的方法列表
methods_to_update = [
    'get_migration_statistics',
    'get_gender_statistics',
    'get_age_distribution',
    'get_education_statistics',
    'get_income_statistics',
    'get_ethnicity_statistics'
]

print("请手动更新以下方法，使用execute_query替代直接的cursor.execute")
for method in methods_to_update:
    print(f"  - {method}")

