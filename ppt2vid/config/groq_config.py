from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GroqConfig:
    """Configuration for Groq API client."""
    api_key: str = os.getenv("GROQ_API_KEY", "")
    model: str = "llama-3.2-90b-vision-preview"
    temperature: float = 1.0
    max_completion_tokens: int = 1024
    top_p: float = 1.0
    stream: bool = False

    def validate(self) -> None:
        """Validate the configuration."""
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set") 