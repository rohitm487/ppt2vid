import pytest
from pathlib import Path
import tempfile
import shutil

from ppt2vid.core.ppt_converter import PPTConverter
from ppt2vid.models.slide import Presentation

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_ppt_converter_initialization(temp_dir):
    """Test PPTConverter initialization."""
    converter = PPTConverter(temp_dir)
    assert converter.output_dir == temp_dir
    assert converter.output_dir.exists()

def test_convert_to_images(temp_dir):
    """Test converting PPT to images."""
    # Create a simple PPT file for testing
    # Note: In a real test, you would need a sample PPT file
    converter = PPTConverter(temp_dir)
    
    # Test with a non-existent file
    with pytest.raises(FileNotFoundError):
        converter.convert_to_images(Path("nonexistent.pptx"))
    
    # Test with an invalid file
    with pytest.raises(Exception):
        converter.convert_to_images(Path(__file__))  # Using this test file as an invalid PPT

def test_save_slide_as_image(temp_dir):
    """Test saving a slide as an image."""
    converter = PPTConverter(temp_dir)
    output_path = temp_dir / "test_slide.png"
    
    # Test with invalid slide object
    with pytest.raises(AttributeError):
        converter._save_slide_as_image(None, output_path) 