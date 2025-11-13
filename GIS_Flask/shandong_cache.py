#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
山东省数据缓存管理器
定期从数据库更新缓存，使用JSON文件存储，避免阻塞主程序
"""
import threading
import time
import json
import os
from datetime import datetime, timedelta
from shandong_stats import ShandongStatistics


class ShandongCacheManager:
    """山东省缓存管理器"""
    
    def __init__(self, update_interval=1800):
        """
        初始化缓存管理器
        :param update_interval: 更新间隔（秒），默认30分钟
        """
        self.cache = {}
        self.lock = threading.Lock()
        self.update_interval = update_interval
        self.last_update = None
        self.next_update = None
        self.stats = ShandongStatistics()
        
        # JSON缓存文件路径
        self.cache_file = os.path.join(
            os.path.dirname(__file__),
            'cache',
            'shandong_cache.json'
        )
        
        # 确保cache目录存在
        cache_dir = os.path.dirname(self.cache_file)
        os.makedirs(cache_dir, exist_ok=True)
        
        print("🚀 初始化山东省缓存管理器...")
        
        # 从JSON文件加载缓存（如果存在），不阻塞
        self.load_from_file()
        
        # 启动后台更新线程（异步更新，不阻塞）
        self.start_background_update()
        
        # 如果缓存为空或过期，触发一次更新（在后台线程中）
        if not self.cache or self.is_cache_expired():
            print("📥 缓存为空或已过期，后台线程将自动更新...")
    
    def load_from_file(self):
        """从JSON文件加载缓存（不阻塞）"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                with self.lock:
                    self.cache = data.get('cache', {})
                    if data.get('last_update'):
                        self.last_update = datetime.strptime(
                            data['last_update'], 
                            '%Y-%m-%d %H:%M:%S'
                        )
                    if data.get('next_update'):
                        self.next_update = datetime.strptime(
                            data['next_update'],
                            '%Y-%m-%d %H:%M:%S'
                        )
                
                print(f"✅ 从文件加载缓存成功（{self.cache_file}）")
                if self.cache:
                    print(f"   - 总人口: {self.cache.get('total_population', 0):,} 人")
                    print(f"   - 最后更新: {data.get('last_update', 'N/A')}")
            else:
                print("📝 缓存文件不存在，将创建新缓存")
        except Exception as e:
            print(f"⚠️ 加载缓存文件失败: {e}")
            self.cache = {}
    
    def save_to_file(self):
        """保存缓存到JSON文件"""
        try:
            data = {
                'cache': self.cache,
                'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None,
                'next_update': self.next_update.strftime('%Y-%m-%d %H:%M:%S') if self.next_update else None,
                'update_interval': self.update_interval
            }
            
            # 使用临时文件，然后原子性替换
            temp_file = self.cache_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
            os.rename(temp_file, self.cache_file)
            
            print(f"💾 缓存已保存到文件: {self.cache_file}")
        except Exception as e:
            print(f"⚠️ 保存缓存文件失败: {e}")
    
    def is_cache_expired(self):
        """检查缓存是否过期"""
        if not self.last_update or not self.next_update:
            return True
        return datetime.now() >= self.next_update
    
    def update_cache(self):
        """更新缓存数据（在后台线程中执行，不阻塞主程序）"""
        print(f"\n{'='*60}")
        print(f"🔄 开始更新山东省缓存 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # 获取统计数据（使用磁盘表，不使用内存表）
            print("📊 正在调用 get_comprehensive_statistics()...")
            data = self.stats.get_comprehensive_statistics()
            print(f"✅ get_comprehensive_statistics() 完成")
            
            # 验证数据
            if not data:
                print("⚠️ 返回的数据为空，使用默认值")
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
            
            # 线程安全地更新缓存
            print("🔒 正在更新缓存（加锁）...")
            with self.lock:
                self.cache = data
                self.last_update = datetime.now()
                self.next_update = self.last_update + timedelta(seconds=self.update_interval)
            print("✅ 缓存更新完成（解锁）")
            
            # 保存到JSON文件
            print("💾 正在保存缓存到文件...")
            self.save_to_file()
            print("✅ 缓存文件保存完成")
            
            duration = time.time() - start_time
            
            print(f"✅ 山东省缓存更新完成！")
            print(f"⏱️  耗时: {duration:.2f} 秒")
            print(f"📦 缓存数据统计:")
            print(f"   - 总人口: {data.get('total_population', 0):,} 人")
            print(f"   - 城市数: {len(data.get('city_population', {}))} 个")
            print(f"   - 婚姻记录: {data.get('marriage', {}).get('total', 0):,} 条")
            print(f"   - 死亡记录: {data.get('death', {}).get('total', 0):,} 条")
            if self.next_update:
                print(f"🕐 下次更新时间: {self.next_update.strftime('%Y-%m-%d %H:%M:%S')} ({self.update_interval//60}分钟后)")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"❌ 更新山东省缓存失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 即使失败，也尝试保存一个空的缓存结构，避免重复失败
            try:
                with self.lock:
                    if not self.cache:
                        self.cache = {
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
            except:
                pass
    
    def get_cache(self):
        """获取缓存数据（线程安全）"""
        with self.lock:
            return self.cache.copy()
    
    def get_cache_info(self):
        """获取缓存信息"""
        with self.lock:
            return {
                'last_update': self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else None,
                'next_update': self.next_update.strftime('%Y-%m-%d %H:%M:%S') if self.next_update else None,
                'update_interval': self.update_interval,
                'total_population': self.cache.get('total_population', 0),
                'total_cities': len(self.cache.get('city_population', {}))
            }
    
    def force_update(self):
        """强制更新缓存（在后台线程中执行，不阻塞）"""
        print("\n⚡ 收到强制更新请求（山东省）...")
        # 在后台线程中执行更新，不阻塞主程序
        update_thread = threading.Thread(
            target=self.update_cache,
            daemon=True,
            name="ShandongForceUpdate"
        )
        update_thread.start()
        print("📥 更新任务已在后台线程中启动，不阻塞主程序...")
    
    def background_update_loop(self):
        """后台更新循环（不阻塞主程序）"""
        try:
            # 如果缓存为空或过期，立即更新一次
            if not self.cache or self.is_cache_expired():
                print("🚀 后台线程：缓存为空或已过期，立即更新...")
                try:
                    self.update_cache()
                except Exception as e:
                    print(f"❌ 后台线程首次更新失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 然后按间隔定期更新
            while True:
                time.sleep(self.update_interval)
                print(f"\n⏰ 定时更新触发（山东省）- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                try:
                    self.update_cache()
                except Exception as e:
                    print(f"❌ 后台线程定时更新失败: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"❌ 后台更新循环异常: {e}")
            import traceback
            traceback.print_exc()
    
    def start_background_update(self):
        """启动后台更新线程"""
        update_thread = threading.Thread(
            target=self.background_update_loop,
            daemon=True,
            name="ShandongCacheUpdater"
        )
        update_thread.start()
        print(f"✅ 山东省后台更新线程已启动（间隔: {self.update_interval//60}分钟）")


# 全局缓存管理器实例
_shandong_cache_manager = None


def get_shandong_cache_manager(update_interval=1800):
    """获取山东省缓存管理器单例"""
    global _shandong_cache_manager
    if _shandong_cache_manager is None:
        _shandong_cache_manager = ShandongCacheManager(update_interval)
    return _shandong_cache_manager

