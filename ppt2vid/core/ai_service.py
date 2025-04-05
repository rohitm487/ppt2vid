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

    def generate_script(self, ocr_text: str) -> str:
        """Generate a lecture-style script from the slide text.
        
        Args:
            ocr_text: Extracted text from the slide
            
        Returns:
            Generated script for the slide
        """
        messages = [
            {
                "role": "system",
                "content": "You are an expert lecturer who explains complex topics in a clear, engaging, and concise manner. Your speaking style is professional yet conversational, making the content accessible while maintaining academic rigor."
            },
            {
                "role": "user",
                "content": f"""Create a natural, lecture-style script for this slide content. The script should sound like a professor explaining the concepts to students:

Slide Content:
{ocr_text}

Requirements:
1. Write as if you're giving a live lecture to students
2. Start with a clear explanation of the main concept
3. Use a professional but conversational tone
4. Include brief examples or analogies where appropriate
5. Keep explanations concise but thorough
6. Connect ideas logically
7. Avoid filler words or unnecessary repetition
8. End with a clear conclusion or transition
9. Maximum length: 2-3 sentences for simple slides, 4-5 for complex ones
10. Focus on explaining 'why' and 'how', not just 'what'

Format:
- Write only the spoken content
- No narration markers, pauses, or directions
- No introductory phrases like "In this slide..." or "Let's look at..."
- Start directly with the explanation"""
            }
        ]

        return self._call_groq_api(messages) 