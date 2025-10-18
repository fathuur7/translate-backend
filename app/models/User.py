from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from app.config.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(100), primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    picture = Column(String(500))
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
