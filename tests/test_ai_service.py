import pytest
from pathlib import Path
import tempfile
import shutil

from ppt2vid.config.groq_config import GroqConfig
from ppt2vid.core.ai_service import AIService
from ppt2vid.models.slide import Slide

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_slide(temp_dir):
    """Create a sample slide for testing."""
    image_path = temp_dir / "test_slide.png"
    # Create a simple image file
    with open(image_path, "wb") as f:
        f.write(b"dummy image data")
    return Slide(slide_id=1, image_path=image_path)

def test_ai_service_initialization():
    """Test AIService initialization."""
    config = GroqConfig()
    service = AIService(config)
    assert service.config == config
    assert service.client is not None

def test_extract_text(sample_slide):
    """Test text extraction from image."""
    config = GroqConfig()
    service = AIService(config)
    
    # Test with non-existent image
    with pytest.raises(FileNotFoundError):
        service.extract_text(Path("nonexistent.png"))
    
    # Test with invalid image
    with pytest.raises(Exception):
        service.extract_text(sample_slide.image_path)

def test_generate_summary(sample_slide):
    """Test image summary generation."""
    config = GroqConfig()
    service = AIService(config)
    
    # Test with non-existent image
    with pytest.raises(FileNotFoundError):
        service.generate_summary(Path("nonexistent.png"))
    
    # Test with invalid image
    with pytest.raises(Exception):
        service.generate_summary(sample_slide.image_path)

def test_generate_script(sample_slide):
    """Test script generation."""
    config = GroqConfig()
    service = AIService(config)
    
    # Test with slide missing OCR text
    with pytest.raises(ValueError):
        service.generate_script(sample_slide)
    
    # Add OCR text and summary
    sample_slide.ocr_text = "Sample OCR text"
    sample_slide.summary = "Sample summary"
    
    # Test with valid slide
    with pytest.raises(Exception):  # Will fail due to invalid API key in test
        service.generate_script(sample_slide) 