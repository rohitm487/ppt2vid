from pydantic import BaseModel
from typing import Optional, List, Dict
from pathlib import Path

class SlideResponse(BaseModel):
    """Response model for a single slide."""
    slide_id: int
    image_path: str
    ocr_text: Optional[str] = None
    summary: Optional[str] = None
    script: Optional[str] = None

class PresentationResponse(BaseModel):
    """Response model for a complete presentation."""
    title: str
    slides: List[SlideResponse]

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str

class ProcessingStatus(BaseModel):
    """Status response model."""
    status: str
    message: str
    progress: Optional[float] = None
    current_slide: Optional[int] = None
    total_slides: Optional[int] = None 