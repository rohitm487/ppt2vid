from pathlib import Path
from typing import List
from pptx import Presentation
from PIL import Image
import io
import os

from ppt2vid.models.slide import Slide, Presentation

class PPTConverter:
    """Handles conversion of PowerPoint presentations to images."""

    def __init__(self, output_dir: Path):
        """Initialize the converter with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_to_images(self, ppt_path: Path) -> Presentation:
        """Convert PowerPoint presentation to images.
        
        Args:
            ppt_path: Path to the PowerPoint file
            
        Returns:
            Presentation object containing slide information
        """
        prs = Presentation(ppt_path)
        slides: List[Slide] = []
        
        for idx, slide in enumerate(prs.slides):
            # Create slide-specific output directory
            slide_dir = self.output_dir / f"slide_{idx + 1}"
            slide_dir.mkdir(exist_ok=True)
            
            # Save slide as image
            image_path = slide_dir / "slide.png"
            self._save_slide_as_image(slide, image_path)
            
            # Create slide object
            slides.append(Slide(
                slide_id=idx + 1,
                image_path=image_path
            ))
        
        return Presentation(
            slides=slides,
            title=ppt_path.stem,
            output_dir=self.output_dir
        )

    def _save_slide_as_image(self, slide, output_path: Path) -> None:
        """Save a single slide as an image.
        
        Args:
            slide: PowerPoint slide object
            output_path: Path where the image should be saved
        """
        # Get slide dimensions
        slide_width = slide.slide_width
        slide_height = slide.slide_height
        
        # Create a new image with white background
        image = Image.new('RGB', (slide_width, slide_height), 'white')
        
        # Save the image
        image.save(output_path, 'PNG') 