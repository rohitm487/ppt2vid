import argparse
from pathlib import Path
import json
from typing import Dict

from ppt2vid.config.groq_config import GroqConfig
from ppt2vid.core.ppt_converter import PPTConverter
from ppt2vid.core.ai_service import AIService
from ppt2vid.models.slide import Presentation

def process_presentation(ppt_path: Path, output_dir: Path) -> Dict:
    """Process a PowerPoint presentation and generate video scripts.
    
    Args:
        ppt_path: Path to the PowerPoint file
        output_dir: Directory to save output files
        
    Returns:
        Dictionary containing the final presentation script
    """
    # Initialize services
    config = GroqConfig()
    ppt_converter = PPTConverter(output_dir)
    ai_service = AIService(config)

    # Convert PPT to images
    presentation = ppt_converter.convert_to_images(ppt_path)
    
    # Process each slide
    for slide in presentation.slides:
        # Extract text using OCR
        slide.ocr_text = ai_service.extract_text(slide.image_path)
        
        # Generate image summary
        slide.summary = ai_service.generate_summary(slide.image_path)
        
        # Generate script
        slide.script = ai_service.generate_script(slide)
    
    # Convert to dictionary format
    result = presentation.to_dict()
    
    # Save results
    output_file = output_dir / "presentation_script.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    
    return result

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Convert PowerPoint to video script")
    parser.add_argument("ppt_path", type=Path, help="Path to the PowerPoint file")
    parser.add_argument("--output-dir", type=Path, default=Path("output"),
                       help="Directory to save output files")
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process presentation
    result = process_presentation(args.ppt_path, args.output_dir)
    
    print(f"Processing complete. Results saved to {args.output_dir}/presentation_script.json")

if __name__ == "__main__":
    main() 