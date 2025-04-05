from pathlib import Path
from typing import Optional
from groq import Groq
import base64

from ppt2vid.config.groq_config import GroqConfig
from ppt2vid.models.slide import Slide

class AIService:
    """Handles AI-related tasks using Groq API."""

    def __init__(self, config: GroqConfig):
        """Initialize the AI service with configuration."""
        self.config = config
        self.config.validate()
        self.client = Groq(api_key=config.api_key)

    def extract_text(self, image_path: Path) -> str:
        """Extract text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Extracted text from the image
        """
        # Read and encode image
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare messages for OCR
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all visible text from this image. Include any text in charts, diagrams, or other visual elements."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

        # Call Groq API
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            stream=self.config.stream,
            stop=self.config.stop
        )

        return response.choices[0].message.content

    def generate_summary(self, image_path: Path) -> str:
        """Generate a summary of the image content.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Summary of the image content
        """
        # Read and encode image
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Prepare messages for summarization
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Provide a detailed summary of this slide image. Focus on visual elements, layout, and overall message. Include any important graphics, charts, or diagrams."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ]

        # Call Groq API
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            stream=self.config.stream,
            stop=self.config.stop
        )

        return response.choices[0].message.content

    def generate_script(self, slide: Slide) -> str:
        """Generate a script for a slide combining OCR text and summary.
        
        Args:
            slide: Slide object containing OCR text and summary
            
        Returns:
            Generated script for the slide
        """
        if not slide.ocr_text or not slide.summary:
            raise ValueError("OCR text and summary must be available to generate script")

        messages = [
            {
                "role": "user",
                "content": f"""Create a coherent script for this slide based on the following information:

OCR Text:
{slide.ocr_text}

Image Summary:
{slide.summary}

Please create a natural, flowing script that:
1. Combines the text and visual information seamlessly
2. Maintains a professional tone
3. Is suitable for narration
4. Highlights key points
5. Provides context and transitions"""
            }
        ]

        # Call Groq API
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
            stream=self.config.stream,
            stop=self.config.stop
        )

        return response.choices[0].message.content 