import zoneinfo
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    username = Column(String,unique=True)
    password = Column(String)

    history = relationship("History", back_populates="user_rel")

def get_tashkent_time():
    tz = zoneinfo.ZoneInfo("Asia/Tashkent")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

class History(Base):
    __tablename__ = "histories"
    id = Column(Integer,primary_key=True,index=True)
    user_question = Column(String)
    ai_response = Column(String)
    created_at = Column(String, default=get_tashkent_time)

    user_rel = relationship("User", back_populates="history")
    user = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))






