"""
Flask GIS 可视化系统主应用
基于内存缓存的高性能GIS可视化服务
"""

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from cache_manager import get_cache_manager
from shandong_cache import get_shandong_cache_manager
from query_handler import QueryHandler
import json
import os
from datetime import datetime

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS，允许跨域请求

# 配置
app.config['JSON_AS_ASCII'] = False  # 支持中文
app.config['JSON_SORT_KEYS'] = False  # 保持键的顺序

# 初始化缓存管理器（10分钟更新一次）
cache_manager = get_cache_manager(update_interval=600)

# 初始化山东省缓存管理器（30分钟更新一次）
shandong_cache_manager = get_shandong_cache_manager(update_interval=1800)

# 初始化查询处理器
query_handler = QueryHandler()

# ==================== 页面路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """仪表板页面"""
    return render_template('dashboard.html')

@app.route('/query')
def query_page():
    """智能查询页面"""
    return render_template('query.html')

@app.route('/shandong')
def shandong_page():
    """山东省数据页面"""
    return render_template('shandong.html')

@app.route('/static/maps/<path:filename>')
def serve_map_data(filename):
    """提供地图数据文件"""
    maps_dir = os.path.join(os.path.dirname(__file__), 'static', 'maps')
    return send_from_directory(maps_dir, filename)

# ==================== API路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'service': 'GIS Visualization API'
    })

@app.route('/api/cache/info', methods=['GET'])
def cache_info():
    """
    获取缓存信息
    """
    try:
        info = cache_manager.get_cache_info()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': info
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取缓存信息失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/cache/update', methods=['POST'])
def force_update():
    """
    强制更新缓存
    """
    try:
        cache_manager.force_update()
        return jsonify({
            'code': 200,
            'message': '缓存更新已触发',
            'data': cache_manager.get_cache_info()
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新缓存失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/all', methods=['GET'])
def get_all_data():
    """
    获取所有缓存数据
    """
    try:
        cache = cache_manager.get_cache()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': cache
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/population', methods=['GET'])
def get_population():
    """
    获取人口数据
    查询参数:
    - province: 省份名称（可选）
    """
    try:
        province = request.args.get('province')
        cache = cache_manager.get_cache()
        
        if province:
            # 返回特定省份数据
            data = cache_manager.get_province_data(province, 'population')
            if data is None:
                return jsonify({
                    'code': 404,
                    'message': f'未找到省份: {province}',
                    'data': None
                }), 404
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'province': province,
                    'population': data
                }
            })
        else:
            # 返回所有省份数据
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': cache.get('population', {})
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取人口数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/density', methods=['GET'])
def get_density():
    """
    获取人口密度数据
    """
    try:
        province = request.args.get('province')
        cache = cache_manager.get_cache()
        
        if province:
            data = cache_manager.get_province_data(province, 'density')
            if data is None:
                return jsonify({
                    'code': 404,
                    'message': f'未找到省份: {province}',
                    'data': None
                }), 404
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'province': province,
                    'density': data
                }
            })
        else:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': cache.get('density', {})
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取密度数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/marriage', methods=['GET'])
def get_marriage():
    """
    获取婚姻数据
    """
    try:
        province = request.args.get('province')
        cache = cache_manager.get_cache()
        
        if province:
            data = cache_manager.get_province_data(province, 'marriage')
            if data is None:
                return jsonify({
                    'code': 404,
                    'message': f'未找到省份: {province}',
                    'data': None
                }), 404
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'province': province,
                    'marriage': data
                }
            })
        else:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': cache.get('marriage', {})
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取婚姻数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/migration', methods=['GET'])
def get_migration():
    """
    获取人口迁移数据
    查询参数:
    - limit: 限制返回数量（可选）
    """
    try:
        limit = request.args.get('limit', type=int)
        cache = cache_manager.get_cache()
        migration = cache.get('migration', [])
        
        if limit:
            migration = migration[:limit]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'migrations': migration,
                'summary': cache.get('migration_summary', {})
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取迁移数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/gender', methods=['GET'])
def get_gender():
    """
    获取性别统计数据
    """
    try:
        province = request.args.get('province')
        cache = cache_manager.get_cache()
        
        if province:
            data = cache_manager.get_province_data(province, 'gender')
            if data is None:
                return jsonify({
                    'code': 404,
                    'message': f'未找到省份: {province}',
                    'data': None
                }), 404
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'province': province,
                    'gender': data
                }
            })
        else:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': cache.get('gender', {})
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取性别数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/age', methods=['GET'])
def get_age():
    """
    获取年龄分布数据
    """
    try:
        province = request.args.get('province')
        cache = cache_manager.get_cache()
        
        if province:
            data = cache_manager.get_province_data(province, 'age')
            if data is None:
                return jsonify({
                    'code': 404,
                    'message': f'未找到省份: {province}',
                    'data': None
                }), 404
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'province': province,
                    'age': data
                }
            })
        else:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': cache.get('age', {})
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取年龄数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/ethnicity', methods=['GET'])
def get_ethnicity():
    """
    获取民族分布数据
    """
    try:
        province = request.args.get('province')
        cache = cache_manager.get_cache()
        
        if province:
            data = cache_manager.get_province_data(province, 'ethnicity')
            if data is None:
                return jsonify({
                    'code': 404,
                    'message': f'未找到省份: {province}',
                    'data': None
                }), 404
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'province': province,
                    'ethnicity': data
                }
            })
        else:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': cache.get('ethnicity', {})
            })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取民族数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/data/summary', methods=['GET'])
def get_summary():
    """
    获取全国汇总数据
    """
    try:
        cache = cache_manager.get_cache()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'national': cache.get('national_summary', {}),
                'top_rankings': cache.get('top_rankings', {}),
                'province_list': cache.get('province_list', []),
                'update_time': cache.get('update_time', '')
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取汇总数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/provinces', methods=['GET'])
def get_provinces():
    """
    获取所有省份列表
    """
    try:
        cache = cache_manager.get_cache()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': cache.get('province_list', [])
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取省份列表失败: {str(e)}',
            'data': None
        }), 500

# ==================== 智能查询API ====================

@app.route('/api/query/manual', methods=['POST'])
def manual_query():
    """
    手动SQL查询
    请求体: {
        "sql": "SELECT ... ",
        "use_memory": true/false (可选，默认true)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'sql' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少SQL参数',
                'data': None
            }), 400
        
        sql = data['sql'].strip()
        use_memory = data.get('use_memory', True)
        
        # 安全检查：禁止危险操作
        sql_upper = sql.upper()
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        if any(keyword in sql_upper for keyword in dangerous_keywords):
            return jsonify({
                'code': 403,
                'message': '禁止执行修改数据的SQL语句',
                'data': None
            }), 403
        
        # 执行查询
        success, results, duration, error = query_handler.execute_sql(sql, use_memory)
        
        if success:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'sql': sql,
                    'results': results,
                    'execution_time': round(duration, 4),
                    'use_memory': use_memory
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': f'SQL执行失败: {error}',
                'data': {
                    'sql': sql,
                    'error': error
                }
            }), 500
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'处理请求失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/query/nl', methods=['POST'])
def nl_query():
    """
    自然语言查询
    请求体: {
        "question": "用户问题",
        "use_memory": true/false (可选，默认true)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'code': 400,
                'message': '缺少question参数',
                'data': None
            }), 400
        
        question = data['question'].strip()
        use_memory = data.get('use_memory', True)
        
        if not question:
            return jsonify({
                'code': 400,
                'message': '问题不能为空',
                'data': None
            }), 400
        
        # 处理自然语言查询
        result = query_handler.process_nl_query(question, use_memory)
        
        if result['success']:
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'question': question,
                    'sql': result['sql'],
                    'sql_generation_time': round(result['sql_generation_time'], 4),
                    'sql_execution_time': round(result['sql_execution_time'], 4),
                    'results': result['query_results'],
                    'answer': result['answer'],
                    'use_memory': use_memory
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': f'查询失败: {result["error"]}',
                'data': {
                    'question': question,
                    'error': result['error']
                }
            }), 500
    
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'处理请求失败: {str(e)}',
            'data': None
        }), 500

# ==================== 山东省数据API ====================

@app.route('/api/shandong/data/all', methods=['GET'])
def get_shandong_all_data():
    """获取山东省所有数据"""
    try:
        print("\n" + "="*60)
        print("📥 API请求: /api/shandong/data/all")
        print("="*60)
        
        data = shandong_cache_manager.get_cache()
        
        # 调试日志：检查数据结构
        print("📦 返回的数据结构:")
        print(f"   - total_population: {data.get('total_population', 'undefined')}")
        print(f"   - city_population: {type(data.get('city_population', None)).__name__}")
        print(f"   - gender: {type(data.get('gender', None)).__name__}")
        print(f"   - marriage: {type(data.get('marriage', None)).__name__}")
        print(f"   - death: {type(data.get('death', None)).__name__}")
        print(f"   - migration: {type(data.get('migration', None)).__name__}")
        print(f"   - income: {type(data.get('income', None)).__name__}")
        
        # 确保所有必需字段都存在
        if not data:
            print("⚠️ 缓存数据为空，返回默认值")
            data = {
                'total_population': 0,
                'city_population': {},
                'gender': {'male': 0, 'female': 0, 'ratio': 0},
                'age': {'0-18': 0, '18-35': 0, '35-60': 0, '60+': 0},
                'education': {},
                'marriage': {'total': 0, 'by_year': {}},
                'death': {'total': 0, 'by_year': {}},
                'income': {'count': 0, 'avg': 0, 'max': 0, 'min': 0},
                'ethnicity': {},
                'migration': {'inflow': 0, 'outflow': 0, 'net': 0, 'inflow_from': {}, 'outflow_to': {}}
            }
        
        print("✅ 数据准备完成，返回响应")
        print("="*60 + "\n")
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        print(f"❌ 获取山东省数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'code': 500,
            'message': f'获取山东省数据失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/shandong/cache/info', methods=['GET'])
def get_shandong_cache_info():
    """获取山东省缓存信息"""
    try:
        info = shandong_cache_manager.get_cache_info()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': info
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取缓存信息失败: {str(e)}',
            'data': None
        }), 500

@app.route('/api/shandong/cache/update', methods=['POST'])
def force_update_shandong_cache():
    """强制更新山东省缓存"""
    try:
        shandong_cache_manager.force_update()
        return jsonify({
            'code': 200,
            'message': '山东省缓存更新成功',
            'data': None
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新失败: {str(e)}',
            'data': None
        }), 500

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'code': 404,
        'message': '请求的资源不存在',
        'data': None
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'code': 500,
        'message': '服务器内部错误',
        'data': None
    }), 500

# ==================== 启动应用 ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Flask GIS 可视化系统启动中...")
    print("="*60)
    print("\n📊 系统信息:")
    print(f"   - 服务地址: http://127.0.0.1:5050")
    print(f"   - API文档: http://127.0.0.1:5050/api/health")
    print(f"   - 缓存更新: 每 10 分钟")
    print(f"   - CORS: 已启用")
    print("\n💡 API端点:")
    print(f"   - GET  /api/health          健康检查")
    print(f"   - GET  /api/cache/info      缓存信息")
    print(f"   - POST /api/cache/update    强制更新")
    print(f"   - GET  /api/data/all        所有数据")
    print(f"   - GET  /api/data/population 人口数据")
    print(f"   - GET  /api/data/density    人口密度")
    print(f"   - GET  /api/data/marriage   婚姻数据")
    print(f"   - GET  /api/data/migration  迁移数据")
    print(f"   - GET  /api/data/gender     性别数据")
    print(f"   - GET  /api/data/age        年龄数据")
    print(f"   - GET  /api/data/ethnicity  民族数据")
    print(f"   - GET  /api/data/summary    汇总数据")
    print(f"   - GET  /api/provinces       省份列表")
    print(f"   - POST /api/query/manual    手动SQL查询")
    print(f"   - POST /api/query/nl        自然语言查询")
    print(f"   - GET  /api/shandong/data/all    山东省所有数据")
    print(f"   - GET  /api/shandong/cache/info  山东省缓存信息")
    print(f"   - POST /api/shandong/cache/update 强制更新山东省缓存")
    print("\n" + "="*60)
    print("✅ 系统就绪，按 Ctrl+C 停止服务")
    print("="*60 + "\n")
    
    # 启动Flask应用
    app.run(
        host='127.0.0.1',
        port=5050,
        debug=True,
        threaded=True
    )


