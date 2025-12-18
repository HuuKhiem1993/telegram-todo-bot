import logging
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters,
    ContextTypes
)
from telegram.constants import ParseMode
import config
from database import db
from keyboards import TodoKeyboards
from utils import formatter, date_utils
from datetime import datetime

# Cấu hình logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States cho ConversationHandler
TITLE, DESCRIPTION, CATEGORY, PRIORITY, DUE_DATE = range(5)

class TodoBot:
    def __init__(self):
        self.application = None
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Lưu thông tin user vào database
        session = db.get_session()
        db_user = db.get_or_create_user(
            session, 
            user.id, 
            user.username, 
            user.first_name, 
            user.last_name
        )
        session.close()
        
        welcome_text = f"""👋 Xin chào *{user.first_name}*!

Tôi là *TodoBot* - trợ lý quản lý công việc của bạn.

📌 *Các tính năng chính:*
• 📝 Tạo và quản lý công việc
• 📂 Phân loại theo danh mục
• 🏷️ Đánh dấu độ ưu tiên
• 🔔 Nhắc nhở thông minh
• 📊 Theo dõi tiến độ

📖 *Các lệnh có sẵn:*
/start - Khởi động bot
/todo - Menu chính
/new - Thêm việc mới
/list - Xem danh sách
/today - Việc hôm nay
/help - Trợ giúp

Hãy bắt đầu bằng cách nhấn vào nút bên dưới!"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.main_menu()
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /help"""
        help_text = """🆘 *Hướng dẫn sử dụng TodoBot*

📌 *Cách thêm công việc:*
1. Nhấn "➕ Thêm việc mới"
2. Nhập tiêu đề
3. Nhập mô tả (tùy chọn)
4. Chọn danh mục
5. Chọn độ ưu tiên
6. Đặt hạn chót

📌 *Quản lý công việc:*
• ✅ Nhấn vào công việc để xem chi tiết
• ✅ Hoàn thành: đánh dấu đã làm xong
• ✏️ Sửa: chỉnh sửa thông tin
• 🗑️ Xóa: xóa công việc
• 📅 Hẹn giờ: đặt thông báo

📌 *Danh mục:*
• Tạo danh mục để phân loại
• Mỗi danh mục có màu riêng
• Có thể chỉnh sửa hoặc xóa

💡 *Mẹo sử dụng:*
• Dùng độ ưu tiên để sắp xếp công việc
• Đặt hạn chót để nhận nhắc nhở
• Xuất dữ liệu định kỳ để backup

Cần hỗ trợ thêm? Liên hệ @admin_username"""
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.main_menu()
        )
    
    async def todo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /todo - Hiển thị menu chính"""
        await update.message.reply_text(
            "📋 *Menu chính*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.main_menu()
        )
    
    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý lệnh /today - Hiển thị công việc hôm nay"""
        session = db.get_session()
        user = session.query(db.User).filter_by(telegram_id=update.effective_user.id).first()
        
        if not user:
            await update.message.reply_text("❌ Không tìm thấy thông tin người dùng!")
            session.close()
            return
        
        today = datetime.now().date()
        tasks = session.query(db.Task).filter(
            db.Task.user_id == user.id,
            db.Task.due_date >= today,
            db.Task.due_date < today + timedelta(days=1),
            db.Task.completed == False
        ).order_by(db.Task.priority, db.Task.due_date).all()
        
        if tasks:
            text = f"📅 *Công việc hôm nay ({today.strftime('%d/%m/%Y')})*\n\n"
            text += formatter.format_tasks_list(tasks)
        else:
            text = "🎉 Không có công việc nào cần làm hôm nay!"
        
        session.close()
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.main_menu()
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xử lý tất cả callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        session = db.get_session()
        user = session.query(db.User).filter_by(telegram_id=user_id).first()
        
        if not user:
            await query.edit_message_text("❌ Lỗi: Không tìm thấy người dùng!")
            session.close()
            return
        
        # Xử lý các callback khác nhau
        if data == "main_menu":
            await self.show_main_menu(query)
        
        elif data == "view_tasks":
            await self.show_tasks_list(query, session, user)
        
        elif data == "add_task":
            await self.start_add_task(query, context)
        
        elif data.startswith("task_detail_"):
            task_id = int(data.split("_")[2])
            await self.show_task_detail(query, session, task_id)
        
        elif data.startswith("complete_"):
            task_id = int(data.split("_")[1])
            await self.complete_task(query, session, task_id)
        
        elif data.startswith("delete_task_"):
            task_id = int(data.split("_")[2])
            await self.confirm_delete_task(query, task_id)
        
        elif data.startswith("confirm_delete_"):
            task_id = int(data.split("_")[2])
            await self.delete_task(query, session, task_id)
        
        elif data.startswith("page_"):
            page = int(data.split("_")[1])
            await self.show_tasks_list(query, session, user, page)
        
        elif data == "settings":
            await self.show_settings(query)
        
        elif data.startswith("set_priority_"):
            parts = data.split("_")
            task_id = int(parts[2])
            priority = int(parts[3])
            await self.set_task_priority(query, session, task_id, priority)
        
        elif data.startswith("set_category_"):
            parts = data.split("_")
            task_id = int(parts[2])
            category_id = int(parts[3])
            await self.set_task_category(query, session, task_id, category_id)
        
        elif data.startswith("set_duedate_"):
            parts = data.split("_")
            task_id = int(parts[2])
            date_str = parts[3]
            await self.set_task_duedate(query, session, task_id, date_str)
        
        elif data == "manage_categories":
            await self.show_categories(query, session, user)
        
        session.close()
    
    async def show_main_menu(self, query):
        """Hiển thị menu chính"""
        await query.edit_message_text(
            "📋 *Menu chính*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.main_menu()
        )
    
    async def show_tasks_list(self, query, session, user, page=0):
        """Hiển thị danh sách công việc"""
        tasks = session.query(db.Task).filter_by(user_id=user.id).order_by(
            db.Task.completed,
            db.Task.priority,
            db.Task.due_date
        ).all()
        
        if not tasks:
            await query.edit_message_text(
                "📭 Bạn chưa có công việc nào!\n\nNhấn '➕ Thêm việc mới' để bắt đầu.",
                reply_markup=TodoKeyboards.main_menu()
            )
            return
        
        # Phân trang
        tasks_per_page = 5
        total_pages = (len(tasks) + tasks_per_page - 1) // tasks_per_page
        
        text = f"📋 *Danh sách công việc* (Trang {page + 1}/{total_pages})\n\n"
        text += formatter.format_tasks_list(tasks)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.task_list(tasks, page, tasks_per_page)
        )
    
    async def show_task_detail(self, query, session, task_id):
        """Hiển thị chi tiết công việc"""
        task = session.query(db.Task).filter_by(id=task_id).first()
        
        if not task:
            await query.answer("❌ Công việc không tồn tại!", show_alert=True)
            return
        
        text = formatter.format_task(task)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.task_detail(task_id)
        )
    
    async def complete_task(self, query, session, task_id):
        """Đánh dấu công việc đã hoàn thành"""
        task = session.query(db.Task).filter_by(id=task_id).first()
        
        if not task:
            await query.answer("❌ Công việc không tồn tại!", show_alert=True)
            return
        
        task.completed = not task.completed  # Toggle trạng thái
        session.commit()
        
        status = "đã hoàn thành" if task.completed else "chưa hoàn thành"
        await query.answer(f"✅ Công việc {status}!")
        
        # Cập nhật lại view
        await self.show_task_detail(query, session, task_id)
    
    async def confirm_delete_task(self, query, task_id):
        """Xác nhận xóa công việc"""
        await query.edit_message_text(
            "🗑️ *Xác nhận xóa*\n\nBạn có chắc chắn muốn xóa công việc này?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.confirm_delete(task_id)
        )
    
    async def delete_task(self, query, session, task_id):
        """Xóa công việc"""
        task = session.query(db.Task).filter_by(id=task_id).first()
        
        if task:
            session.delete(task)
            session.commit()
            await query.answer("🗑️ Công việc đã bị xóa!", show_alert=True)
        
        await self.show_tasks_list(query, session, task.user)
    
    async def start_add_task(self, query, context):
        """Bắt đầu quá trình thêm công việc mới"""
        await query.edit_message_text(
            "📝 *Thêm công việc mới*\n\nVui lòng nhập *tiêu đề* công việc:",
            parse_mode=ParseMode.MARKDOWN
        )
        context.user_data['adding_task'] = True
        return TITLE
    
    async def show_settings(self, query):
        """Hiển thị menu cài đặt"""
        await query.edit_message_text(
            "⚙️ *Cài đặt*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.settings_menu()
        )
    
    async def set_task_priority(self, query, session, task_id, priority):
        """Thiết lập độ ưu tiên cho task"""
        task = session.query(db.Task).filter_by(id=task_id).first()
        
        if task:
            task.priority = priority
            session.commit()
            await query.answer(f"🏷️ Đã đặt độ ưu tiên!", show_alert=True)
            await self.show_task_detail(query, session, task_id)
    
    async def set_task_category(self, query, session, task_id, category_id):
        """Thiết lập danh mục cho task"""
        task = session.query(db.Task).filter_by(id=task_id).first()
        category = session.query(db.Category).filter_by(id=category_id).first()
        
        if task and category:
            task.category = category
            session.commit()
            await query.answer(f"📂 Đã chọn danh mục: {category.name}!", show_alert=True)
            await self.show_task_detail(query, session, task_id)
    
    async def set_task_duedate(self, query, session, task_id, date_str):
        """Thiết lập hạn chót cho task"""
        task = session.query(db.Task).filter_by(id=task_id).first()
        due_date = date_utils.parse_date(date_str)
        
        if task and due_date:
            task.due_date = due_date
            session.commit()
            await query.answer(f"📅 Đã đặt hạn chót: {date_utils.format_date(due_date)}!", show_alert=True)
            await self.show_task_detail(query, session, task_id)
    
    async def show_categories(self, query, session, user):
        """Hiển thị danh sách danh mục"""
        categories = session.query(db.Category).filter_by(user_id=user.id).all()
        
        if not categories:
            text = "📂 Bạn chưa có danh mục nào!"
        else:
            text = "📂 *Danh sách danh mục*\n\n"
            for cat in categories:
                task_count = session.query(db.Task).filter_by(category_id=cat.id).count()
                text += f"• {cat.name}: {task_count} công việc\n"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.main_menu()
        )
    
    # Conversation handlers cho thêm task
    async def receive_task_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận tiêu đề task"""
        context.user_data['task_title'] = update.message.text
        
        await update.message.reply_text(
            "📝 *Tiêu đề đã lưu!*\n\nVui lòng nhập *mô tả* (hoặc /skip để bỏ qua):",
            parse_mode=ParseMode.MARKDOWN
        )
        return DESCRIPTION
    
    async def skip_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bỏ qua mô tả"""
        context.user_data['task_description'] = ""
        
        # Lấy danh sách danh mục
        session = db.get_session()
        user = session.query(db.User).filter_by(telegram_id=update.effective_user.id).first()
        categories = session.query(db.Category).filter_by(user_id=user.id).all()
        session.close()
        
        await update.message.reply_text(
            "📂 *Chọn danh mục:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.category_buttons(categories)
        )
        return CATEGORY
    
    async def receive_task_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận mô tả task"""
        context.user_data['task_description'] = update.message.text
        
        # Lấy danh sách danh mục
        session = db.get_session()
        user = session.query(db.User).filter_by(telegram_id=update.effective_user.id).first()
        categories = session.query(db.Category).filter_by(user_id=user.id).all()
        session.close()
        
        await update.message.reply_text(
            "📂 *Chọn danh mục:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.category_buttons(categories)
        )
        return CATEGORY
    
    async def receive_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận category từ callback"""
        query = update.callback_query
        await query.answer()
        
        context.user_data['category_id'] = int(query.data.split("_")[2])
        
        await query.edit_message_text(
            "🏷️ *Chọn độ ưu tiên:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.priority_buttons()
        )
        return PRIORITY
    
    async def receive_priority(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận priority từ callback"""
        query = update.callback_query
        await query.answer()
        
        context.user_data['priority'] = int(query.data.split("_")[1])
        
        await query.edit_message_text(
            "📅 *Chọn hạn chót:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=TodoKeyboards.due_date_buttons()
        )
        return DUE_DATE
    
    async def receive_duedate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận due date từ callback"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "custom_date":
            await query.edit_message_text(
                "📅 Vui lòng nhập ngày (định dạng YYYY-MM-DD):\n\nVí dụ: 2024-12-31",
                parse_mode=ParseMode.MARKDOWN
            )
            return DUE_DATE
        
        date_str = query.data.split("_")[1]
        context.user_data['due_date'] = date_str
        
        # Lưu task vào database
        await self.save_task(update, context)
        return ConversationHandler.END
    
    async def receive_custom_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Nhận ngày tùy chỉnh"""
        try:
            date_str = update.message.text
            datetime.strptime(date_str, "%Y-%m-%d")  # Validate
            context.user_data['due_date'] = date_str
            
            # Lưu task vào database
            await self.save_task(update, context)
            return ConversationHandler.END
        except ValueError:
            await update.message.reply_text(
                "❌ Định dạng ngày không hợp lệ!\nVui lòng nhập theo định dạng YYYY-MM-DD:"
            )
            return DUE_DATE
    
    async def save_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lưu task vào database"""
        # Lấy dữ liệu từ context
        task_data = context.user_data
        
        # Tạo task mới
        session = db.get_session()
        user = session.query(db.User).filter_by(
            telegram_id=update.effective_user.id
        ).first()
        
        due_date = date_utils.parse_date(task_data.get('due_date'))
        
        task = db.Task(
            user_id=user.id,
            category_id=task_data.get('category_id'),
            title=task_data.get('task_title'),
            description=task_data.get('task_description', ''),
            priority=task_data.get('priority', 2),
            due_date=due_date
        )
        
        session.add(task)
        session.commit()
        session.close()
        
        # Xóa dữ liệu tạm
        context.user_data.clear()
        
        # Gửi thông báo thành công
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "✅ *Công việc đã được thêm thành công!*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=TodoKeyboards.main_menu()
            )
        else:
            await update.message.reply_text(
                "✅ *Công việc đã được thêm thành công!*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=TodoKeyboards.main_menu()
            )
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Hủy bỏ conversation"""
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Đã hủy thêm công việc.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    def run(self):
        """Khởi chạy bot"""
        # Tạo application
        self.application = Application.builder().token(config.Config.BOT_TOKEN).build()
        
        # Thêm command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("todo", self.todo_command))
        self.application.add_handler(CommandHandler("today", self.today_command))
        self.application.add_handler(CommandHandler("new", self.start_add_task))
        
        # Thêm conversation handler cho thêm task
        conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_add_task, pattern="^add_task$"),
                CommandHandler("new", self.start_add_task)
            ],
            states={
                TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_task_title)],
                DESCRIPTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_task_description),
                    CommandHandler("skip", self.skip_description)
                ],
                CATEGORY: [CallbackQueryHandler(self.receive_category, pattern="^select_category_")],
                PRIORITY: [CallbackQueryHandler(self.receive_priority, pattern="^priority_")],
                DUE_DATE: [
                    CallbackQueryHandler(self.receive_duedate, pattern="^duedate_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_custom_date)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
        
        self.application.add_handler(conv_handler)
        
        # Thêm callback query handler
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Chạy bot
        print("🤖 Bot đang chạy...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    bot = TodoBot()
    bot.run()