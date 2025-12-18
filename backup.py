import sqlite3
import shutil
import schedule
import time
from datetime import datetime
import os

class BackupManager:
    def __init__(self, db_path, backup_dir="backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
    
    def create_backup(self):
        """Tạo backup database"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.backup_dir}/todo_backup_{timestamp}.db"
        
        # Sao chép file database
        shutil.copy2(self.db_path, backup_path)
        
        # Giữ chỉ 7 backup gần nhất
        self.cleanup_old_backups()
        
        return backup_path
    
    def cleanup_old_backups(self, keep=7):
        """Xóa các backup cũ"""
        backups = sorted(
            [f for f in os.listdir(self.backup_dir) if f.startswith("todo_backup_")],
            reverse=True
        )
        
        for old_backup in backups[keep:]:
            os.remove(f"{self.backup_dir}/{old_backup}")
    
    def schedule_backups(self):
        """Lập lịch backup tự động"""
        # Backup hàng ngày lúc 2:00 sáng
        schedule.every().day.at("02:00").do(self.create_backup)
        
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Kiểm tra mỗi giờ