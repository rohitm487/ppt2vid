from pathlib import Path
import os
import json
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AuthConfig:
    def __init__(self):
        self.google_client_id: Optional[str] = None
        self.google_client_secret: Optional[str] = None
        self.load_config()

    def load_config(self):
        # First try to load from environment variables
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        # If not found in env vars, try to load from config file
        if not self.google_client_id or not self.google_client_secret:
            config_file = Path("config/auth_config.json")
            if config_file.exists():
                try:
                    with config_file.open() as f:
                        config = json.load(f)
                        self.google_client_id = config.get("google_client_id")
                        self.google_client_secret = config.get("google_client_secret")
                except Exception as e:
                    print(f"Error loading auth config: {e}")

        # Validate configuration
        if not self.google_client_id or not self.google_client_secret:
            raise ValueError(
                "Google OAuth credentials not found. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                "environment variables or provide them in config/auth_config.json"
            )

    @staticmethod
    def create_default_config():
        """Create a default config file if it doesn't exist."""
        config_dir = Path("config")
        config_file = config_dir / "auth_config.json"
        
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        
        if not config_file.exists():
            default_config = {
                "google_client_id": "YOUR_GOOGLE_CLIENT_ID",
                "google_client_secret": "YOUR_GOOGLE_CLIENT_SECRET"
            }
            
            with config_file.open("w") as f:
                json.dump(default_config, f, indent=2)
            
            print(f"Created default config file at {config_file}")
            print("Please update it with your Google OAuth credentials") 