#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据同步脚本：从持久化表同步到内存表
定期运行以保持内存数据最新
"""
import pymysql
import time
from datetime import datetime
from typing import Dict, Tuple

# 数据库配置
MYSQL_CONFIG = {

}

class MemoryDBSync:
    """内存数据库同步管理器"""
    
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**MYSQL_CONFIG)
            print("✅ 数据库连接成功")
            
            # 设置内存表大小限制
            self.set_memory_limits()
            
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def set_memory_limits(self):
        """设置内存表大小限制"""
        cursor = self.connection.cursor()
        try:
            # 10GB 内存限制
            memory_limit = 20737418240
            
            print(f"🔧 设置内存表大小限制: {memory_limit / 1024 / 1024 / 1024:.1f} GB")
            
            # 尝试设置全局变量（需要 SUPER 权限）
            try:
                cursor.execute(f"SET GLOBAL max_heap_table_size = {memory_limit}")
                cursor.execute(f"SET GLOBAL tmp_table_size = {memory_limit}")
                print("   ✅ 全局设置成功")
            except pymysql.err.OperationalError as e:
                if "Access denied" in str(e):
                    print("   ⚠️  无 SUPER 权限，跳过全局设置")
                else:
                    raise
            
            # 设置当前会话变量（总是可以）
            cursor.execute(f"SET SESSION max_heap_table_size = {memory_limit}")
            cursor.execute(f"SET SESSION tmp_table_size = {memory_limit}")
            print("   ✅ 会话设置成功")
            
        except Exception as e:
            print(f"   ⚠️  设置内存限制失败: {e}")
        finally:
            cursor.close()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("🔌 数据库连接已关闭")
    
    def sync_table(self, source_table: str, target_table: str) -> Tuple[bool, int, float]:
        """
        同步单个表
        :param source_table: 源表名（InnoDB）
        :param target_table: 目标表名（MEMORY）
        :return: (成功标志, 记录数, 耗时秒数)
        """
        start_time = time.time()
        cursor = self.connection.cursor()
        
        try:
            print(f"\n{'='*60}")
            print(f"📊 同步表: {source_table} → {target_table}")
            print(f"{'='*60}")
            
            # 1. 重建内存表（应用新的内存限制）
            print(f"🔧 重建内存表（应用新的内存限制）...")
            cursor.execute(f"ALTER TABLE {target_table} ENGINE=MEMORY")
            
            # 2. 清空内存表
            print(f"🗑️  清空目标表...")
            cursor.execute(f"TRUNCATE TABLE {target_table}")
            
            # 3. 获取源表数据量
            cursor.execute(f"SELECT COUNT(*) FROM {source_table}")
            total_count = cursor.fetchone()[0]
            print(f"📈 源表记录数: {total_count:,}")
            
            if total_count == 0:
                print(f"⚠️  源表为空，跳过同步")
                return True, 0, 0.0
            
            # 4. 批量复制数据（使用 INSERT ... SELECT）
            print(f"📥 开始批量复制...")
            copy_sql = f"INSERT INTO {target_table} SELECT * FROM {source_table}"
            cursor.execute(copy_sql)
            self.connection.commit()
            
            # 5. 验证数据量
            cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
            memory_count = cursor.fetchone()[0]
            
            duration = time.time() - start_time
            
            if memory_count == total_count:
                print(f"✅ 同步成功！")
                print(f"   - 记录数: {memory_count:,}")
                print(f"   - 耗时: {duration:.2f} 秒")
                print(f"   - 速度: {memory_count/duration:.0f} 条/秒")
                return True, memory_count, duration
            else:
                print(f"⚠️  数据量不一致！")
                print(f"   - 源表: {total_count:,}")
                print(f"   - 内存表: {memory_count:,}")
                return False, memory_count, duration
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ 同步失败: {str(e)}")
            self.connection.rollback()
            return False, 0, duration
        finally:
            cursor.close()
    
    def update_sync_metadata(self, table_name: str, success: bool, 
                            record_count: int, duration: float, 
                            error_msg: str = None):
        """
        更新同步元数据
        """
        cursor = self.connection.cursor()
        try:
            sql = """
                UPDATE memory_sync_metadata 
                SET last_sync_time = %s,
                    record_count = %s,
                    sync_duration_seconds = %s,
                    sync_status = %s,
                    error_message = %s
                WHERE table_name = %s
            """
            status = 'success' if success else 'failed'
            cursor.execute(sql, (
                datetime.now(),
                record_count,
                duration,
                status,
                error_msg,
                table_name
            ))
            self.connection.commit()
        except Exception as e:
            print(f"⚠️  更新元数据失败: {e}")
        finally:
            cursor.close()
    
    def sync_all_tables(self):
        """同步所有表"""
        print("\n" + "="*60)
        print("🚀 开始同步所有表到内存数据库")
        print("="*60)
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        overall_start = time.time()
        
        # 定义同步表映射
        table_mappings = [
            ('population', 'population_memory'),
            ('population_deceased', 'population_deceased_memory'),
            ('marriage_info', 'marriage_info_memory')
        ]
        
        results = []
        
        for source, target in table_mappings:
            success, count, duration = self.sync_table(source, target)
            results.append({
                'table': target,
                'success': success,
                'count': count,
                'duration': duration
            })
            
            # 更新元数据
            error_msg = None if success else "同步失败"
            self.update_sync_metadata(target, success, count, duration, error_msg)
            
            # 短暂休息，避免数据库压力
            time.sleep(1)
        
        # 总结
        total_duration = time.time() - overall_start
        
        print("\n" + "="*60)
        print("📊 同步完成统计")
        print("="*60)
        
        total_records = 0
        success_count = 0
        
        for result in results:
            status = "✅ 成功" if result['success'] else "❌ 失败"
            print(f"{status} | {result['table']:<30} | {result['count']:>10,} 条 | {result['duration']:>6.2f} 秒")
            
            if result['success']:
                success_count += 1
                total_records += result['count']
        
        print("="*60)
        print(f"✅ 成功: {success_count}/{len(results)} 个表")
        print(f"📦 总记录数: {total_records:,} 条")
        print(f"⏱️  总耗时: {total_duration:.2f} 秒")
        print(f"⚡ 平均速度: {total_records/total_duration:.0f} 条/秒")
        print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        return success_count == len(results)
    
    def get_memory_stats(self):
        """获取内存表统计信息"""
        cursor = self.connection.cursor()
        try:
            print("\n" + "="*60)
            print("📈 内存表统计信息")
            print("="*60)
            
            sql = """
                SELECT 
                    table_name AS '表名',
                    engine AS '引擎',
                    table_rows AS '行数',
                    ROUND(data_length / 1024 / 1024, 2) AS '数据(MB)',
                    ROUND(index_length / 1024 / 1024, 2) AS '索引(MB)',
                    ROUND((data_length + index_length) / 1024 / 1024, 2) AS '总计(MB)'
                FROM information_schema.tables
                WHERE table_schema = 'population' 
                AND table_name LIKE '%_memory'
                ORDER BY table_name
            """
            
            cursor.execute(sql)
            results = cursor.fetchall()
            
            for row in results:
                print(f"\n表名: {row[0]}")
                print(f"  引擎: {row[1]}")
                print(f"  行数: {row[2]:,}")
                print(f"  数据大小: {row[3]} MB")
                print(f"  索引大小: {row[4]} MB")
                print(f"  总大小: {row[5]} MB")
            
            # 显示同步元数据
            print("\n" + "="*60)
            print("🔄 同步历史记录")
            print("="*60)
            
            cursor.execute("""
                SELECT 
                    table_name,
                    last_sync_time,
                    record_count,
                    sync_duration_seconds,
                    sync_status
                FROM memory_sync_metadata
                ORDER BY table_name
            """)
            
            for row in cursor.fetchall():
                print(f"\n{row[0]}:")
                print(f"  上次同步: {row[1]}")
                print(f"  记录数: {row[2]:,}")
                print(f"  耗时: {row[3]:.2f} 秒")
                print(f"  状态: {row[4]}")
            
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
        finally:
            cursor.close()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🗄️  内存数据库同步工具")
    print("="*60)
    
    syncer = MemoryDBSync()
    
    try:
        # 连接数据库
        if not syncer.connect():
            return
        
        # 同步所有表
        success = syncer.sync_all_tables()
        
        # 显示统计信息
        syncer.get_memory_stats()
        
        if success:
            print("\n✅ 所有表同步完成！")
        else:
            print("\n⚠️  部分表同步失败，请检查错误信息")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        syncer.close()


if __name__ == '__main__':
    main()

