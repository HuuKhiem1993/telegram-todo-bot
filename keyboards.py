from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta

class TodoKeyboards:
    @staticmethod
    def main_menu():
        """Bàn phím menu chính"""
        keyboard = [
            [InlineKeyboardButton("📝 Xem việc cần làm", callback_data="view_tasks")],
            [InlineKeyboardButton("➕ Thêm việc mới", callback_data="add_task")],
            [InlineKeyboardButton("📂 Danh mục", callback_data="manage_categories")],
            [InlineKeyboardButton("⚙️ Cài đặt", callback_data="settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_list(tasks, page=0, tasks_per_page=5):
        """Bàn phím danh sách công việc"""
        keyboard = []
        
        # Hiển thị tasks trên trang hiện tại
        start_idx = page * tasks_per_page
        end_idx = start_idx + tasks_per_page
        current_tasks = tasks[start_idx:end_idx]
        
        for task in current_tasks:
            status = "✅" if task.completed else "⬜"
            priority_icons = {1: "🔴", 2: "🟡", 3: "🟢"}
            priority_icon = priority_icons.get(task.priority, "🟡")
            
            button_text = f"{status} {priority_icon} {task.title[:30]}"
            keyboard.append([InlineKeyboardButton(
                button_text, 
                callback_data=f"task_detail_{task.id}"
            )])
        
        # Nút điều hướng
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"page_{page-1}"))
        if end_idx < len(tasks):
            nav_buttons.append(InlineKeyboardButton("Sau ➡️", callback_data=f"page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Nút quay lại
        keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def task_detail(task_id):
        """Bàn phím chi tiết công việc"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Hoàn thành", callback_data=f"complete_{task_id}"),
                InlineKeyboardButton("✏️ Sửa", callback_data=f"edit_task_{task_id}")
            ],
            [
                InlineKeyboardButton("🗑️ Xóa", callback_data=f"delete_task_{task_id}"),
                InlineKeyboardButton("📅 Hẹn giờ", callback_data=f"set_reminder_{task_id}")
            ],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="view_tasks")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def priority_buttons(task_id=None):
        """Bàn phím chọn độ ưu tiên"""
        callback_prefix = f"set_priority_{task_id}_" if task_id else "priority_"
        
        keyboard = [
            [
                InlineKeyboardButton("🔴 Cao", callback_data=f"{callback_prefix}1"),
                InlineKeyboardButton("🟡 Trung bình", callback_data=f"{callback_prefix}2"),
                InlineKeyboardButton("🟢 Thấp", callback_data=f"{callback_prefix}3")
            ]
        ]
        if task_id:
            keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data=f"task_detail_{task_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def category_buttons(categories, task_id=None):
        """Bàn phím chọn danh mục"""
        keyboard = []
        callback_prefix = f"set_category_{task_id}_" if task_id else "select_category_"
        
        for category in categories:
            keyboard.append([InlineKeyboardButton(
                f"■ {category.name}", 
                callback_data=f"{callback_prefix}{category.id}"
            )])
        
        if task_id:
            keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data=f"task_detail_{task_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def due_date_buttons(task_id=None):
        """Bàn phím chọn ngày đến hạn"""
        today = datetime.now()
        keyboard = []
        
        # Các tùy chọn nhanh
        quick_options = [
            ("Hôm nay", today),
            ("Ngày mai", today + timedelta(days=1)),
            ("Tuần sau", today + timedelta(days=7))
        ]
        
        for text, date in quick_options:
            date_str = date.strftime("%Y-%m-%d")
            callback_data = f"set_duedate_{task_id}_{date_str}" if task_id else f"duedate_{date_str}"
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("📅 Chọn ngày khác", callback_data="custom_date")])
        
        if task_id:
            keyboard.append([InlineKeyboardButton("🔙 Quay lại", callback_data=f"task_detail_{task_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirm_delete(task_id):
        """Bàn phím xác nhận xóa"""
        keyboard = [
            [
                InlineKeyboardButton("✅ Có, xóa", callback_data=f"confirm_delete_{task_id}"),
                InlineKeyboardButton("❌ Không", callback_data=f"task_detail_{task_id}")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def settings_menu():
        """Bàn phím cài đặt"""
        keyboard = [
            [InlineKeyboardButton("👤 Thông tin tài khoản", callback_data="account_info")],
            [InlineKeyboardButton("🔔 Cài đặt thông báo", callback_data="notification_settings")],
            [InlineKeyboardButton("📤 Xuất dữ liệu", callback_data="export_data")],
            [InlineKeyboardButton("🔙 Quay lại", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)