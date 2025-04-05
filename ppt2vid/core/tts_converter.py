import subprocess
from pathlib import Path

def convert_text_to_speech(text: str, output_path: str) -> None:
    """
    Convert text to speech using macOS's say command.
    
    Args:
        text: The text to convert to speech
        output_path: Path to save the audio file
    """
    try:
        subprocess.run([
            'say',
            '-o', output_path,
            '--file-format=AIFF',
            text
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error converting text to speech: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error in text-to-speech conversion: {str(e)}") 