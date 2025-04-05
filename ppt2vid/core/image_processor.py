from pathlib import Path
from typing import List
import re
from PIL import Image
from ppt2vid.models.slide import Slide, Presentation as PresentationModel

class ImageProcessor:
    """Handles processing of sequenced image slides."""

    def __init__(self, output_dir: Path):
        """Initialize the processor with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a directory for slides
        self.slides_dir = self.output_dir / "slides"
        self.slides_dir.mkdir(exist_ok=True)

    def process_images(self, title: str = "slideshow") -> PresentationModel:
        """Process numbered images in the slides directory.
        
        Args:
            title: Title for the slideshow
            
        Returns:
            Presentation object containing slide information
        """
        slides: List[Slide] = []
        
        # Find all image files in the slides directory
        image_files = []
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
            image_files.extend(list(self.slides_dir.glob(f"*{ext}")))
            image_files.extend(list(self.slides_dir.glob(f"*{ext.upper()}")))
        
        if not image_files:
            raise Exception("No image files found in the slides directory")
        
        # Extract numbers from filenames using regex
        numbered_files = []
        for file in image_files:
            # Look for numbers in the filename
            numbers = re.findall(r'\d+', file.stem)
            if numbers:
                # Use the last number found in the filename
                slide_num = int(numbers[-1])
                # Convert image to PNG format for consistency
                png_path = self.slides_dir / f"slide_{slide_num:03d}.png"
                if not png_path.exists():  # Only convert if not already converted
                    try:
                        with Image.open(file) as img:
                            # Convert to RGB if necessary (e.g., for RGBA images)
                            if img.mode in ('RGBA', 'LA'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                background.paste(img, mask=img.split()[-1])
                                img = background
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')
                            # Save as PNG
                            img.save(png_path, 'PNG', quality=95)
                    except Exception as e:
                        print(f"Error converting {file}: {e}")
                        continue
                    # Delete original file after successful conversion
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"Error deleting original file {file}: {e}")
                numbered_files.append((slide_num, png_path))
        
        if not numbered_files:
            raise Exception("No numbered image files found. Image filenames should contain numbers.")
        
        # Sort files by their extracted numbers
        numbered_files.sort()  # This will sort by the slide_num
        
        # Create slide objects in order
        for idx, (_, image_path) in enumerate(numbered_files, 1):
            slides.append(Slide(
                slide_id=idx,
                image_path=image_path
            ))
        
        return PresentationModel(
            slides=slides,
            title=title,
            output_dir=self.output_dir
        ) 