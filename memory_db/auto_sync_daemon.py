#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内存数据库自动同步守护进程
定期从持久化表同步到内存表
"""
import time
import schedule
from datetime import datetime
from sync_to_memory import MemoryDBSync

# 配置
SYNC_INTERVAL_MINUTES = 30  # 每30分钟同步一次
AUTO_SYNC_ON_STARTUP = True  # 启动时立即同步


class SyncDaemon:
    """同步守护进程"""
    
    def __init__(self, interval_minutes=30):
        self.interval_minutes = interval_minutes
        self.syncer = MemoryDBSync()
        self.last_sync_time = None
        self.sync_count = 0
        
    def sync_task(self):
        """执行同步任务"""
        try:
            print("\n" + "="*60)
            print(f"⏰ 定时同步任务触发 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 这是第 {self.sync_count + 1} 次同步")
            print("="*60)
            
            # 连接数据库
            if not self.syncer.connect():
                print("❌ 数据库连接失败，跳过本次同步")
                return
            
            # 执行同步
            success = self.syncer.sync_all_tables()
            
            # 更新状态
            self.last_sync_time = datetime.now()
            self.sync_count += 1
            
            # 关闭连接
            self.syncer.close()
            
            if success:
                print(f"\n✅ 第 {self.sync_count} 次同步成功")
                next_time = datetime.now()
                next_time = next_time.replace(
                    minute=(next_time.minute + self.interval_minutes) % 60
                )
                print(f"⏭️  下次同步时间: {next_time.strftime('%H:%M:%S')}")
            else:
                print(f"\n⚠️  第 {self.sync_count} 次同步部分失败")
                
        except Exception as e:
            print(f"\n❌ 同步任务执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def start(self):
        """启动守护进程"""
        print("\n" + "="*60)
        print("🚀 内存数据库自动同步守护进程")
        print("="*60)
        print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  同步间隔: {self.interval_minutes} 分钟")
        print(f"🔄 启动时同步: {'是' if AUTO_SYNC_ON_STARTUP else '否'}")
        print("="*60)
        
        # 启动时立即同步
        if AUTO_SYNC_ON_STARTUP:
            print("\n📥 执行启动同步...")
            self.sync_task()
        
        # 设置定时任务
        schedule.every(self.interval_minutes).minutes.do(self.sync_task)
        
        print(f"\n✅ 守护进程已启动，每 {self.interval_minutes} 分钟同步一次")
        print("💡 按 Ctrl+C 停止守护进程\n")
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(10)  # 每10秒检查一次
        except KeyboardInterrupt:
            print("\n\n⚠️  守护进程已停止")
            print(f"📊 总共执行了 {self.sync_count} 次同步")
            if self.last_sync_time:
                print(f"⏰ 最后同步时间: {self.last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    daemon = SyncDaemon(interval_minutes=SYNC_INTERVAL_MINUTES)
    daemon.start()


if __name__ == '__main__':
    main()

