import json

# 读取人口数据
with open('pp.json', 'r', encoding='utf-8') as f:
    population_data = json.load(f)

# 读取行政区划代码数据
with open('pca-code.json', 'r', encoding='utf-8') as f:
    pca_data = json.load(f)

# 生成新的数据结构
result = {}

# 遍历每个省份
for province in pca_data:
    province_code = province['code']
    province_name = province['name']
    
    # 去掉"省"、"市"、"自治区"、"特别行政区"等后缀来匹配人口数据
    short_name = province_name.replace('省', '').replace('市', '').replace('自治区', '').replace('特别行政区', '')
    
    # 获取人口数（如果有的话）
    population = population_data.get(short_name, 0)
    
    # 收集所有6位的地址码及其对应的省市区
    code_mapping = {}
    
    # 遍历市级数据
    if 'children' in province:
        for city in province['children']:
            city_name = city['name']
            
            # 遍历区县级数据
            if 'children' in city:
                for district in city['children']:
                    district_code = district['code']
                    district_name = district['name']
                    
                    # 只保留6位的地址码
                    if len(district_code) == 6:
                        # 构建完整的地址：省-市-区
                        full_address = f"{province_name}-{city_name}-{district_name}"
                        code_mapping[district_code] = full_address
    
    # 构建结果
    result[short_name] = {
        "人口数": population,
        "地址码": code_mapping
    }

# 保存结果
with open('province_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("数据处理完成！已生成 province_data.json 文件")
print(f"共处理 {len(result)} 个省级行政区")

# 统计总的地址码数量
total_codes = sum(len(data['地址码']) for data in result.values())
print(f"共收集 {total_codes} 个6位地址码")

# 打印前3个省份作为示例
count = 0
for province_name, data in result.items():
    if count < 3:
        print(f"\n{province_name}:")
        print(f"  人口数: {data['人口数']}")
        print(f"  地址码数量: {len(data['地址码'])}")
        # 打印前3个地址码作为示例
        sample_count = 0
        for code, address in data['地址码'].items():
            if sample_count < 3:
                print(f"    {code}: {address}")
                sample_count += 1
        count += 1

