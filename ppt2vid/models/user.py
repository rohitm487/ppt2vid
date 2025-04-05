from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from ppt2vid.database import Base

class UserRole(enum.Enum):
    SUPERUSER = "superuser"
    PREMIUM = "premium"
    BASIC = "basic"

class SubscriptionTier(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True)
    name = Column(String)
    picture = Column(String)
    role = Column(Enum(UserRole), default=UserRole.BASIC)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    videos_generated = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    videos = relationship("Video", back_populates="user")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processing_status = Column(String)

    user = relationship("User", back_populates="videos") 