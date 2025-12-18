import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot token từ BotFather
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # ID admin (lấy từ @userinfobot trên Telegram)
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 0))
    
    # Cấu hình database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///todo_bot.db")
    
    # Mã hóa (dùng để mã hóa dữ liệu nhạy cảm)
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "default-secret-key-change-me")
    
    # Cài đặt thời gian
    TIMEZONE = "Asia/Ho_Chi_Minh"