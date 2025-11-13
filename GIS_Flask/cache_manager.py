"""
内存缓存管理模块
实现数据的内存缓存和定时更新机制
"""

import threading
import time
from datetime import datetime
from typing import Dict, Any
import sys
import os

# 添加父目录到路径，以便导入data_statistics
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from GIS.data_statistics import PopulationStatistics


class CacheManager:
    """内存缓存管理器"""
    
    def __init__(self, update_interval=600):
        """
        初始化缓存管理器
        :param update_interval: 更新间隔（秒），默认600秒=10分钟
        """
        self.update_interval = update_interval
        self.cache = {}
        self.last_update = None
        self.is_updating = False
        self.lock = threading.Lock()
        self.stats = PopulationStatistics()
        
        # 初始化缓存
        print("🚀 初始化缓存管理器...")
        self.update_cache()
        
        # 启动后台更新线程
        self.start_background_update()
    
    def update_cache(self):
        """更新缓存数据"""
        if self.is_updating:
            print("⏳ 缓存正在更新中，跳过本次更新")
            return
        
        try:
            self.is_updating = True
            start_time = time.time()
            
            print(f"\n{'='*60}")
            print(f"🔄 开始更新缓存 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # 获取所有统计数据
            with self.lock:
                print("📊 正在获取综合统计数据...")
                new_cache = self.stats.get_comprehensive_statistics()
                
                # 额外添加一些优化的数据结构
                print("🔧 正在生成优化数据结构...")
                
                # 1. 省份列表（用于前端下拉菜单）
                new_cache['province_list'] = list(new_cache['population'].keys())
                
                # 2. TOP排行榜（预计算，减少前端计算）
                new_cache['top_rankings'] = {
                    'population_top10': sorted(
                        new_cache['population'].items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10],
                    'density_top10': sorted(
                        new_cache['density'].items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )[:10] if new_cache.get('density') else []
                }
                
                # 3. 迁移统计（预计算流入流出）
                if new_cache.get('migration'):
                    migration_in = {}
                    migration_out = {}
                    for item in new_cache['migration']:
                        # 流入统计
                        to_prov = item['to']
                        migration_in[to_prov] = migration_in.get(to_prov, 0) + item['count']
                        # 流出统计
                        from_prov = item['from']
                        migration_out[from_prov] = migration_out.get(from_prov, 0) + item['count']
                    
                    new_cache['migration_summary'] = {
                        'top_in': sorted(migration_in.items(), key=lambda x: x[1], reverse=True)[:10],
                        'top_out': sorted(migration_out.items(), key=lambda x: x[1], reverse=True)[:10]
                    }
                
                # 4. 全国汇总数据
                new_cache['national_summary'] = {
                    'total_population': sum(new_cache['population'].values()),
                    'total_provinces': len(new_cache['population']),
                    'total_married': sum([v['married_count'] for v in new_cache['marriage'].values()]) if new_cache.get('marriage') else 0,
                    'total_migrations': len(new_cache['migration']) if new_cache.get('migration') else 0
                }
                
                # 更新缓存
                self.cache = new_cache
                self.last_update = datetime.now()
            
            elapsed_time = time.time() - start_time
            
            print(f"✅ 缓存更新完成！")
            print(f"⏱️  耗时: {elapsed_time:.2f} 秒")
            print(f"📦 缓存数据统计:")
            print(f"   - 总人口: {self.cache['national_summary']['total_population']:,} 人")
            print(f"   - 省份数: {self.cache['national_summary']['total_provinces']} 个")
            print(f"   - 已婚人口: {self.cache['national_summary']['total_married']:,} 人")
            print(f"   - 迁移流向: {self.cache['national_summary']['total_migrations']:,} 条")
            print(f"🕐 下次更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (10分钟后)")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ 缓存更新失败: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_updating = False
    
    def get_cache(self) -> Dict[str, Any]:
        """
        获取缓存数据
        :return: 缓存的数据字典
        """
        with self.lock:
            if not self.cache:
                print("⚠️ 缓存为空，触发立即更新")
                self.update_cache()
            return self.cache.copy()
    
    def get_province_data(self, province: str, data_type: str) -> Any:
        """
        获取特定省份的特定类型数据
        :param province: 省份名称
        :param data_type: 数据类型（population, density, marriage等）
        :return: 该省份的数据
        """
        with self.lock:
            cache = self.cache
            if data_type in cache and province in cache[data_type]:
                return cache[data_type][province]
            return None
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        :return: 缓存元信息
        """
        with self.lock:
            return {
                'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None,
                'next_update': (
                    datetime.fromtimestamp(self.last_update.timestamp() + self.update_interval)
                    .strftime('%Y-%m-%d %H:%M:%S')
                ) if self.last_update else None,
                'update_interval': self.update_interval,
                'is_updating': self.is_updating,
                'cache_size': len(str(self.cache)),
                'data_count': {
                    'provinces': len(self.cache.get('population', {})),
                    'migrations': len(self.cache.get('migration', [])),
                    'marriages': len(self.cache.get('marriage', {}))
                }
            }
    
    def background_update_loop(self):
        """后台更新循环"""
        while True:
            try:
                time.sleep(self.update_interval)
                print(f"\n⏰ 定时更新触发 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.update_cache()
            except Exception as e:
                print(f"❌ 后台更新出错: {str(e)}")
                import traceback
                traceback.print_exc()
    
    def start_background_update(self):
        """启动后台更新线程"""
        update_thread = threading.Thread(
            target=self.background_update_loop,
            daemon=True,
            name="CacheUpdateThread"
        )
        update_thread.start()
        print(f"✅ 后台更新线程已启动（每 {self.update_interval} 秒更新一次）\n")
    
    def force_update(self):
        """强制立即更新缓存"""
        print("🔄 收到强制更新请求...")
        self.update_cache()
    
    def clear_cache(self):
        """清空缓存"""
        with self.lock:
            self.cache = {}
            self.last_update = None
            print("🗑️ 缓存已清空")
    
    def close(self):
        """关闭缓存管理器"""
        try:
            self.stats.close()
            print("✅ 缓存管理器已关闭")
        except:
            pass


# 全局缓存管理器实例
_cache_manager = None

def get_cache_manager(update_interval=600) -> CacheManager:
    """
    获取全局缓存管理器实例（单例模式）
    :param update_interval: 更新间隔（秒）
    :return: CacheManager实例
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(update_interval=update_interval)
    return _cache_manager


if __name__ == '__main__':
    # 测试缓存管理器
    print("="*60)
    print("🧪 测试内存缓存管理器")
    print("="*60)
    
    # 创建缓存管理器（60秒更新一次，用于测试）
    cm = CacheManager(update_interval=60)
    
    # 获取缓存信息
    info = cm.get_cache_info()
    print("\n📊 缓存信息:")
    print(f"   最后更新: {info['last_update']}")
    print(f"   下次更新: {info['next_update']}")
    print(f"   更新间隔: {info['update_interval']} 秒")
    print(f"   省份数量: {info['data_count']['provinces']}")
    
    # 获取缓存数据
    cache = cm.get_cache()
    print(f"\n📦 缓存数据键: {list(cache.keys())}")
    
    # 获取特定省份数据
    guangdong_pop = cm.get_province_data('广东', 'population')
    print(f"\n🏙️ 广东省人口: {guangdong_pop:,} 人" if guangdong_pop else "❌ 未找到广东省数据")
    
    print("\n✅ 测试完成！后台线程将持续运行...")
    print("💡 提示: 缓存将每 60 秒自动更新一次")
    
    # 保持运行以观察后台更新
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\n👋 程序退出")
        cm.close()


