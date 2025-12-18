from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    
    # Quan hệ
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    color = Column(String(10), default="#3498db")
    
    # Quan hệ
    user = relationship("User", back_populates="categories")
    tasks = relationship("Task", back_populates="category")

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    completed = Column(Boolean, default=False)
    priority = Column(Integer, default=2)  # 1: Cao, 2: Trung bình, 3: Thấp
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Quan hệ
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")

class Database:
    def __init__(self):
        self.engine = create_engine(config.Config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()
    
    def get_or_create_user(self, session, telegram_id, username, first_name, last_name):
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.commit()
            
            # Tạo categories mặc định
            default_categories = [
                ("Công việc", "#e74c3c"),
                ("Cá nhân", "#3498db"),
                ("Mua sắm", "#2ecc71"),
                ("Học tập", "#f39c12")
            ]
            
            for name, color in default_categories:
                category = Category(user_id=user.id, name=name, color=color)
                session.add(category)
            session.commit()
        
        return user

# Khởi tạo database
db = Database()