#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
下载中国地图JSON数据到本地
"""
import requests
import json
import os

def download_china_map():
    """下载中国地图数据"""
    # 创建static/maps目录
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    maps_dir = os.path.join(static_dir, 'maps')
    os.makedirs(maps_dir, exist_ok=True)
    
    map_file = os.path.join(maps_dir, 'china.json')
    
    print("📥 正在下载中国地图数据...")
    
    # 尝试多个数据源
    data_sources = [
        {
            'name': 'ECharts官方GitHub',
            'url': 'https://raw.githubusercontent.com/apache/echarts/master/map/json/china.json'
        },
        {
            'name': 'DataV备用源',
            'url': 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
        },
        {
            'name': 'GitHub备用源1',
            'url': 'https://raw.githubusercontent.com/lyhmydata1/GeoMapData_CN/master/geojson/100000_full.json'
        }
    ]
    
    for source in data_sources:
        try:
            print(f"🔄 尝试从 {source['name']} 下载...")
            response = requests.get(source['url'], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # 验证数据格式
                if isinstance(data, dict) and ('features' in data or 'type' in data):
                    # 保存到本地
                    with open(map_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ 地图数据下载成功！")
                    print(f"   - 保存路径: {map_file}")
                    
                    # 显示基本信息
                    if 'features' in data:
                        print(f"   - 省份数量: {len(data['features'])}")
                        if data['features']:
                            print(f"   - 示例省份: {data['features'][0].get('properties', {}).get('name', 'N/A')}")
                    
                    return True
                else:
                    print(f"⚠️ 数据格式无效")
            else:
                print(f"⚠️ HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            continue
    
    # 如果所有数据源都失败，创建一个最小化的地图数据
    print("\n⚠️ 所有数据源都失败，创建最小化地图数据...")
    minimal_map = {
        "type": "FeatureCollection",
        "features": []
    }
    
    with open(map_file, 'w', encoding='utf-8') as f:
        json.dump(minimal_map, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已创建空地图文件: {map_file}")
    print("   请手动下载地图数据并替换此文件")
    print("   推荐数据源: https://github.com/apache/echarts/tree/master/map/json")
    
    return False

if __name__ == '__main__':
    download_china_map()


