from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64
import config

class Encryption:
    def __init__(self):
        # Tạo key từ secret
        key = base64.urlsafe_b64encode(config.Config.ENCRYPTION_KEY.ljust(32)[:32].encode())
        self.cipher = Fernet(key)
    
    def encrypt(self, data):
        """Mã hóa dữ liệu"""
        if not data:
            return None
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data):
        """Giải mã dữ liệu"""
        if not encrypted_data:
            return None
        return self.cipher.decrypt(encrypted_data.encode()).decode()

class DateUtils:
    @staticmethod
    def parse_date(date_str):
        """Chuyển đổi string thành datetime"""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None
    
    @staticmethod
    def format_date(date):
        """Định dạng ngày tháng"""
        if not date:
            return "Không có"
        return date.strftime("%d/%m/%Y")
    
    @staticmethod
    def is_overdue(due_date):
        """Kiểm tra quá hạn"""
        if not due_date:
            return False
        return due_date.date() < datetime.now().date()

class TaskFormatter:
    @staticmethod
    def format_task(task):
        """Định dạng hiển thị task"""
        status = "✅ Đã hoàn thành" if task.completed else "⏳ Đang thực hiện"
        priority_text = {1: "🔴 Cao", 2: "🟡 Trung bình", 3: "🟢 Thấp"}.get(task.priority, "🟡 Trung bình")
        
        category_name = task.category.name if task.category else "Không có danh mục"
        due_date_text = DateUtils.format_date(task.due_date)
        
        overdue = DateUtils.is_overdue(task.due_date)
        overdue_text = " ⚠️ QUÁ HẠN" if overdue else ""
        
        return f"""📝 *{task.title}*

📋 Mô tả: {task.description or 'Không có mô tả'}
📂 Danh mục: {category_name}
🏷️ Độ ưu tiên: {priority_text}
📅 Hạn chót: {due_date_text}{overdue_text}
📊 Trạng thái: {status}
🕐 Tạo lúc: {task.created_at.strftime('%d/%m/%Y %H:%M')}
🆔 ID: `{task.id}`
"""
    
    @staticmethod
    def format_tasks_list(tasks):
        """Định dạng danh sách tasks"""
        if not tasks:
            return "📭 Danh sách trống!"
        
        result = []
        for i, task in enumerate(tasks, 1):
            status = "✅" if task.completed else "⬜"
            priority_icons = {1: "🔴", 2: "🟡", 3: "🟢"}
            priority_icon = priority_icons.get(task.priority, "🟡")
            
            overdue = DateUtils.is_overdue(task.due_date)
            overdue_text = " ⚠️" if overdue else ""
            
            result.append(f"{i}. {status} {priority_icon} *{task.title}*{overdue_text}")
        
        return "\n".join(result)

# Khởi tạo utilities
encryption = Encryption()
date_utils = DateUtils()
formatter = TaskFormatter()