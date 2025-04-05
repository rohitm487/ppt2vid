import uvicorn
from pathlib import Path

if __name__ == "__main__":
    # Create temp directory if it doesn't exist
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    
    # Run the FastAPI application
    uvicorn.run(
        "ppt2vid.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 