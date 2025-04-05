# PPT to Video Script Converter

A Python application that converts PowerPoint presentations into detailed video scripts using AI-powered text extraction and summarization.

## Features

- Convert PowerPoint slides to images
- Extract text from slides using OCR
- Generate image summaries
- Create coherent video scripts
- Maintain slide order and context

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
GROQ_API_KEY=your_api_key_here
```

## Usage

```bash
python -m ppt2vid.core.main presentation.pptx
```

## Project Structure

```
ppt2vid/
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

