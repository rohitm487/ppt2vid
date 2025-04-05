from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Union
from ppt2vid.models.user import UserRole, SubscriptionTier
from pydantic import validator

class UserBase(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None

class UserCreate(UserBase):
    google_id: str

class UserResponse(UserBase):
    id: int
    role: UserRole
    subscription_tier: SubscriptionTier
    videos_generated: int
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UserFeatures(BaseModel):
    features: List[str]
    subscription_tier: str
    limits: Dict[str, Union[int, float]]

    @validator('subscription_tier')
    def validate_subscription_tier(cls, v):
        valid_tiers = {'FREE', 'BASIC', 'PREMIUM'}
        if v not in valid_tiers:
            raise ValueError(f"Invalid subscription tier. Must be one of: {valid_tiers}")
        return v

    @validator('limits')
    def validate_limits(cls, v):
        required_keys = {'max_videos_per_day', 'max_slides_per_video', 'max_video_duration'}
        if not all(key in v for key in required_keys):
            raise ValueError(f"Limits must contain all required keys: {required_keys}")
        return v

class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    subscription_tier: Optional[SubscriptionTier] = None

class MessageResponse(BaseModel):
    message: str
    video_path: Optional[str] = None
    scripts: Optional[List[str]] = None

class ProcessingStatus(BaseModel):
    status: str
    message: str
    progress: float
    total_slides: Optional[int] = None
    current_slide: Optional[int] = None

class SlideResponse(BaseModel):
    slide_id: int
    image_path: str
    ocr_text: Optional[str] = None
    summary: Optional[str] = None
    script: Optional[str] = None

class PresentationResponse(BaseModel):
    title: Optional[str] = None
    slides: List[SlideResponse]
    total_slides: int

class ErrorResponse(BaseModel):
    detail: str

class UpgradeRequest(BaseModel):
    payment_method: str
    email: str
    transaction_id: str
    message: Optional[str] = None