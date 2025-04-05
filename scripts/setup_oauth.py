#!/usr/bin/env python3
from pathlib import Path
import json
import sys

def setup_oauth():
    print("Google OAuth Credentials Setup")
    print("-----------------------------")
    print("\nThis script will help you set up your Google OAuth credentials.")
    print("\nFirst, go to the Google Cloud Console (https://console.cloud.google.com)")
    print("1. Create a new project or select an existing one")
    print("2. Enable the Google+ API")
    print("3. Go to the Credentials page")
    print("4. Click 'Create Credentials' and select 'OAuth client ID'")
    print("5. Select 'Web application' as the application type")
    print("6. Add these authorized redirect URIs:")
    print("   - http://localhost:3000/auth/callback")
    print("   - http://localhost:3000")
    print("\nAfter creating the OAuth client, you'll get a client ID and client secret.")
    
    client_id = input("\nEnter your Google Client ID: ").strip()
    client_secret = input("Enter your Google Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("\nError: Both Client ID and Client Secret are required!")
        sys.exit(1)
    
    config_dir = Path("config")
    config_file = config_dir / "auth_config.json"
    
    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the credentials
    config = {
        "google_client_id": client_id,
        "google_client_secret": client_secret
    }
    
    with config_file.open("w") as f:
        json.dump(config, f, indent=2)
    
    print(f"\nCredentials saved to {config_file}")
    print("\nYou can now start the application!")

if __name__ == "__main__":
    setup_oauth() 