from typing import Dict, Optional, Callable
from functools import wraps
from fastapi import HTTPException, Depends
from ppt2vid.models.user import User, UserRole, SubscriptionTier
from ppt2vid.auth import get_current_user

# Role-specific limits
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "max_videos_per_day": 2,
        "max_slides_per_video": 5,
        "max_video_duration": 300,  # 5 minutes
        "features": ["basic_tts"]
    },
    SubscriptionTier.BASIC: {
        "max_videos_per_day": 10,
        "max_slides_per_video": 20,
        "max_video_duration": 900,  # 15 minutes
        "features": ["basic_tts", "custom_scripts"]
    },
    SubscriptionTier.PREMIUM: {
        "max_videos_per_day": -1,  # -1 represents unlimited
        "max_slides_per_video": 100,
        "max_video_duration": 3600,  # 60 minutes
        "features": ["basic_tts", "custom_scripts", "hd_quality", "background_music"]
    }
}

def check_user_limits(user: User, num_slides: Optional[int] = None) -> Dict:
    """Check user's limits based on their subscription tier."""
    limits = TIER_LIMITS[user.subscription_tier]
    
    # Check daily video limit
    max_videos = limits["max_videos_per_day"]
    if max_videos != -1 and user.videos_generated >= max_videos:
        raise HTTPException(
            status_code=403,
            detail=f"Daily video limit ({max_videos}) reached for your subscription tier"
        )
    
    # Check slides limit if provided
    if num_slides and num_slides > limits["max_slides_per_video"]:
        raise HTTPException(
            status_code=403,
            detail=f"Maximum {limits['max_slides_per_video']} slides allowed for your subscription tier"
        )
    
    return limits

def require_feature(feature: str) -> Callable:
    """Decorator to check if user has access to a specific feature."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            limits = TIER_LIMITS[current_user.subscription_tier]
            if feature not in limits["features"]:
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature '{feature}' not available in your subscription tier"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def require_role(required_role: UserRole) -> Callable:
    """Decorator to check if user has the required role."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            role_hierarchy = {
                UserRole.BASIC: 0,
                UserRole.PREMIUM: 1,
                UserRole.SUPERUSER: 2
            }
            
            if role_hierarchy[current_user.role] < role_hierarchy[required_role]:
                raise HTTPException(
                    status_code=403,
                    detail=f"This action requires {required_role.value} role"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

def get_user_features(user: User) -> Dict:
    """Get all features available to the user based on their subscription tier."""
    tier_info = TIER_LIMITS[user.subscription_tier]
    
    # Convert -1 to a large number for unlimited videos
    max_videos = tier_info["max_videos_per_day"]
    if max_videos == -1:
        max_videos = 999999  # Using a large finite number instead of infinity
    
    return {
        "subscription_tier": user.subscription_tier.value.upper(),
        "features": tier_info["features"],
        "limits": {
            "max_videos_per_day": max_videos,
            "max_slides_per_video": tier_info["max_slides_per_video"],
            "max_video_duration": tier_info["max_video_duration"]
        }
    } 