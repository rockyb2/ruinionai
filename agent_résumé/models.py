from database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime,ForeignKey
from datetime import datetime

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    transcription = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    participants = Column(String)
    summary = Column(Text)
    # user_id = Column(Integer, ForeignKey("users.id",ondelete="SET NULL"), nullable=True)



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)