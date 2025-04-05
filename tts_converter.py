import json
import os
from pathlib import Path
import subprocess

def convert_scripts_to_speech(json_file_path: str):
    """
    Convert presentation scripts to speech using macOS's built-in 'say' command.
    Saves audio files and updates the JSON with audio file paths.
    """
    # Create audio directory if it doesn't exist
    audio_dir = Path("audio")
    audio_dir.mkdir(exist_ok=True)
    
    # Load the presentation data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        presentation_data = json.load(f)
    
    # Process each slide
    for slide in presentation_data.get('slides', []):
        if 'script' in slide:
            # Generate unique audio filename using slide ID
            audio_filename = f"slide_{slide['slide_id']}.aiff"
            audio_path = audio_dir / audio_filename
            
            # Use macOS 'say' command to generate speech
            # -v Samantha selects a professional female voice
            # --file-format=AIFF sets high-quality audio format
            subprocess.run([
                'say',
                '-v', 'Samantha',
                '--file-format=AIFF',
                '-o', str(audio_path),
                slide['script']
            ])
            
            # Update JSON with audio path
            slide['audio_path'] = str(audio_path)
    
    # Save updated JSON
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(presentation_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    convert_scripts_to_speech("presentation_results.json") 