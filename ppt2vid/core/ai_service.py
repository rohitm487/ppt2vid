from pathlib import Path
from typing import Optional
import requests
import base64

from ppt2vid.config.groq_config import GroqConfig
from ppt2vid.models.slide import Slide

class AIService:
    """Handles AI-related tasks using Groq API."""

    def __init__(self, config: GroqConfig):
        """Initialize the AI service with configuration."""
        self.config = config
        self.config.validate()
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }

    def _call_groq_api(self, messages: list) -> str:
        """Make a call to the Groq API.
        
        Args:
            messages: List of message objects for the conversation
            
        Returns:
            The response content from the API
        """
        data = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_completion_tokens,
            "top_p": self.config.top_p,
            "stream": self.config.stream
        }

        response = requests.post(self.api_url, headers=self.headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"API call failed with status {response.status_code}: {response.text}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]

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
            image_data_url = f"data:image/png;base64,{encoded_image}"

        # Prepare messages for OCR
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all visible text from this image, including any text in charts, diagrams, or other visual elements."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    }
                ]
            }
        ]

        return self._call_groq_api(messages)

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
            image_data_url = f"data:image/png;base64,{encoded_image}"

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
                            "url": image_data_url
                        }
                    }
                ]
            }
        ]

        return self._call_groq_api(messages)

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
                "content": f"""Create a natural, flowing script for this slide based on the following information. The script should be written as pure spoken content, without any narration markers, pauses, sound effects, or scene directions:

OCR Text:
{slide.ocr_text}

Image Summary:
{slide.summary}

The script should:
1. Flow naturally as spoken content
2. Maintain a professional tone
3. Combine the text and visual information seamlessly
4. Highlight key points effectively
5. Provide smooth transitions between topics
6. Exclude any narration markers (e.g., no "Narrator:", "(pause)", "[Scene:]", etc.)
7. Exclude any sound effects or music cues
8. Focus purely on what would be spoken"""
            }
        ]

        return self._call_groq_api(messages) 