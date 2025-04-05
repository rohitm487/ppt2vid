import json
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import numpy as np
from pathlib import Path
import os

def create_presentation_video(json_file_path: str, output_path: str = "presentation.mp4") -> None:
    """
    Create a video from slides and audio files using moviepy.
    Each slide is shown for the duration of its corresponding audio narration.
    The order of slides and audio is preserved exactly as in the JSON file.
    
    Args:
        json_file_path: Path to the JSON file containing presentation data
        output_path: Path where the output video will be saved
    """
    # Load the presentation data
    with open(json_file_path, 'r') as f:
        presentation_data = json.load(f)
    
    # Create video clips for each slide in order
    clips = []
    total_duration = 0
    
    print("Processing slides in order:")
    for i, slide in enumerate(presentation_data['slides'], 1):
        if 'image_path' in slide and 'audio_path' in slide:
            print(f"Processing slide {i}/{len(presentation_data['slides'])}")
            print(f"Image: {slide['image_path']}")
            print(f"Audio: {slide['audio_path']}")
            
            # Verify files exist
            if not os.path.exists(slide['image_path']):
                raise FileNotFoundError(f"Image file not found: {slide['image_path']}")
            if not os.path.exists(slide['audio_path']):
                raise FileNotFoundError(f"Audio file not found: {slide['audio_path']}")
            
            # Create image clip
            image_clip = ImageClip(slide['image_path'])
            
            # Load audio and get its duration
            audio_clip = AudioFileClip(slide['audio_path'])
            
            # Set the duration of the image clip to match the audio
            image_clip = image_clip.set_duration(audio_clip.duration)
            
            # Add audio to the clip
            video_clip = image_clip.set_audio(audio_clip)
            
            clips.append(video_clip)
            total_duration += audio_clip.duration
            print(f"Slide {i} duration: {audio_clip.duration:.2f} seconds")
    
    if not clips:
        raise ValueError("No valid slides found in the presentation data")
    
    print(f"\nTotal presentation duration: {total_duration:.2f} seconds")
    print("Concatenating clips in order...")
    
    # Concatenate all clips in order
    final_clip = concatenate_videoclips(clips, method="compose")
    
    print(f"Writing final video to {output_path}...")
    # Write the result with high quality settings
    final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac',
                             bitrate='8000k', audio_bitrate='384k')
    
    print("Cleaning up resources...")
    # Close all clips to free up resources
    for clip in clips:
        clip.close()
    final_clip.close()
    
    print("Video creation completed successfully!") 