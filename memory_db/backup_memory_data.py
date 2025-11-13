#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存数据备份脚本
将内存表数据导出为 SQL 和 CSV 格式
防止服务器重启后数据丢失
"""
import pymysql
import csv
import os
from datetime import datetime
from typing import List, Tuple

# 数据库配置
MYSQL_CONFIG = {

}

# 备份目录
BACKUP_DIR = 'memory_db/backups'


class MemoryDataBackup:
    """内存数据备份工具"""
    
    def __init__(self, backup_dir=BACKUP_DIR):
        self.backup_dir = backup_dir
        self.connection = None
        
        # 创建备份目录
        os.makedirs(backup_dir, exist_ok=True)
    
    def connect(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(**MYSQL_CONFIG)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.connection:
            self.connection.close()
    
    def backup_to_csv(self, table_name: str) -> bool:
        """
        导出表为 CSV 格式
        """
        cursor = self.connection.cursor()
        
        try:
            print(f"\n📥 备份表 {table_name} 为 CSV...")
            
            # 获取数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"⚠️  表 {table_name} 为空，跳过备份")
                return True
            
            # 获取列名
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.backup_dir, f"{table_name}_{timestamp}.csv")
            
            # 写入 CSV
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)  # 写入表头
                writer.writerows(rows)    # 写入数据
            
            file_size = os.path.getsize(filename) / 1024 / 1024
            print(f"✅ CSV 备份成功: {filename}")
            print(f"   - 记录数: {len(rows):,}")
            print(f"   - 文件大小: {file_size:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def backup_to_sql(self, table_name: str) -> bool:
        """
        导出表为 SQL 格式
        """
        cursor = self.connection.cursor()
        
        try:
            print(f"\n📥 备份表 {table_name} 为 SQL...")
            
            # 获取数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                print(f"⚠️  表 {table_name} 为空，跳过备份")
                return True
            
            # 获取表结构
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table = cursor.fetchone()[1]
            
            # 获取列名
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            column_list = ', '.join([f"`{col}`" for col in columns])
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.backup_dir, f"{table_name}_{timestamp}.sql")
            
            # 写入 SQL
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"-- 备份时间: {datetime.now()}\n")
                f.write(f"-- 表名: {table_name}\n")
                f.write(f"-- 记录数: {len(rows)}\n\n")
                
                # 表结构
                f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n\n")
                f.write(f"{create_table};\n\n")
                
                # 数据
                f.write(f"-- 数据插入\n")
                batch_size = 1000
                for i in range(0, len(rows), batch_size):
                    batch = rows[i:i+batch_size]
                    f.write(f"INSERT INTO `{table_name}` ({column_list}) VALUES\n")
                    
                    for j, row in enumerate(batch):
                        # 转义值
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, str):
                                escaped = val.replace("'", "\\'")
                                values.append(f"'{escaped}'")
                            else:
                                values.append(str(val))
                        
                        value_str = f"({', '.join(values)})"
                        
                        if j < len(batch) - 1:
                            f.write(f"{value_str},\n")
                        else:
                            f.write(f"{value_str};\n\n")
            
            file_size = os.path.getsize(filename) / 1024 / 1024
            print(f"✅ SQL 备份成功: {filename}")
            print(f"   - 记录数: {len(rows):,}")
            print(f"   - 文件大小: {file_size:.2f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ 备份失败: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def backup_all_tables(self, format='both'):
        """
        备份所有内存表
        :param format: 'csv', 'sql', 'both'
        """
        print("\n" + "="*60)
        print("💾 开始备份内存数据库")
        print("="*60)
        print(f"⏰ 备份时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 备份目录: {self.backup_dir}")
        print(f"📋 备份格式: {format}")
        print("="*60)
        
        tables = [
            'population_memory',
            'population_deceased_memory',
            'marriage_info_memory'
        ]
        
        success_count = 0
        
        for table in tables:
            if format in ('csv', 'both'):
                if self.backup_to_csv(table):
                    success_count += 1
            
            if format in ('sql', 'both'):
                if self.backup_to_sql(table):
                    success_count += 1
        
        print("\n" + "="*60)
        print("📊 备份完成统计")
        print("="*60)
        
        expected = len(tables) * (2 if format == 'both' else 1)
        print(f"✅ 成功: {success_count}/{expected}")
        print(f"📁 备份目录: {self.backup_dir}")
        print("="*60)
        
        # 列出备份文件
        self.list_backups()
    
    def list_backups(self):
        """列出所有备份文件"""
        print("\n📂 现有备份文件:")
        
        files = sorted(os.listdir(self.backup_dir), reverse=True)
        
        if not files:
            print("   (无)")
            return
        
        total_size = 0
        for f in files[:10]:  # 只显示最新的10个
            filepath = os.path.join(self.backup_dir, f)
            size = os.path.getsize(filepath) / 1024 / 1024
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            print(f"   - {f:<50} {size:>8.2f} MB  {mtime.strftime('%Y-%m-%d %H:%M')}")
            total_size += size
        
        if len(files) > 10:
            print(f"   ... 还有 {len(files) - 10} 个文件")
        
        print(f"\n   总大小: {total_size:.2f} MB")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='内存数据库备份工具')
    parser.add_argument('--format', choices=['csv', 'sql', 'both'], 
                       default='both', help='备份格式')
    args = parser.parse_args()
    
    backup = MemoryDataBackup()
    
    try:
        if not backup.connect():
            return
        
        backup.backup_all_tables(format=args.format)
        
        print("\n✅ 备份完成！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 备份失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        backup.close()


if __name__ == '__main__':
    main()

