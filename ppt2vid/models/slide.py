from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

@dataclass
class Slide:
    """Represents a single slide from a PowerPoint presentation."""
    slide_id: int
    image_path: Path
    ocr_text: Optional[str] = None
    summary: Optional[str] = None
    script: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert slide data to dictionary format."""
        return {
            "slide_id": self.slide_id,
            "image_path": str(self.image_path),
            "ocr_text": self.ocr_text,
            "summary": self.summary,
            "script": self.script
        }

@dataclass
class Presentation:
    """Represents a complete PowerPoint presentation."""
    slides: List[Slide]
    title: str
    output_dir: Path

    def to_dict(self) -> dict:
        """Convert presentation data to dictionary format."""
        return {
            "title": self.title,
            "slides": [slide.to_dict() for slide in self.slides]
        } 