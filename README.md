# PPT to Video Script Converter

A Python application that converts PowerPoint presentations into detailed video scripts using AI-powered text extraction and summarization.

## Features

- Convert PowerPoint slides to images
- Extract text from slides using OCR
- Generate image summaries
- Create coherent video scripts
- Maintain slide order and context
- REST API for easy integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rohitm487/ppt2vid.git
cd ppt2vid
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Groq API key:
```
GROQ_API_KEY=api_key
```

## Usage

### Command Line Interface

```bash
python -m ppt2vid.core.main presentation.pptx
```

### REST API

1. Start the API server:
```bash
python run.py
```

2. The API will be available at `http://localhost:8000`

3. API Endpoints:

- **Upload Presentation**
  ```
  POST /upload
  Content-Type: multipart/form-data
  Body: file (PowerPoint file)
  Response: ProcessingStatus
  ```

- **Check Processing Status**
  ```
  GET /status/{processing_id}
  Response: ProcessingStatus
  ```

- **Get Results**
  ```
  GET /result/{processing_id}
  Response: PresentationResponse
  ```

4. Example API Usage:

```python
import requests

# Upload presentation
with open("presentation.pptx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
processing_id = response.json()["processing_id"]

# Check status
status = requests.get(f"http://localhost:8000/status/{processing_id}").json()

# Get results when processing is complete
if status["status"] == "completed":
    results = requests.get(f"http://localhost:8000/result/{processing_id}").json()
```

## Project Structure

```
ppt2vid/
├── api/            # FastAPI application
├── core/           # Core functionality
├── utils/          # Utility functions
├── models/         # Data models
├── config/         # Configuration files
└── tests/          # Test files
```

## Development

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions
- Run tests before committing
- Use meaningful commit messages

## License

MIT License

