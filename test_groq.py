import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get API key from environment
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

# API endpoint
url = "https://api.groq.com/openai/v1/chat/completions"

# Headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Request body
data = {
    "model": "llama-3.2-11b-vision-preview",
    "messages": [
        {
            "role": "user",
            "content": "Hello, how are you?"
        }
    ],
    "temperature": 1.0,
    "max_tokens": 1024,
    "top_p": 1.0,
    "stream": False
}

# Make the request
response = requests.post(url, headers=headers, json=data)

# Check if request was successful
if response.status_code == 200:
    result = response.json()
    print("Response:", result["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}")
    print(response.text) 