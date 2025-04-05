from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import json
from pathlib import Path
import numpy as np

def create_presentation_video(json_file_path: str, output_path: str = "presentation.mp4"):
    """
    Create a video from slides and audio files specified in the JSON file.
    Each slide is shown for the duration of its corresponding audio narration.
    """
    # Load the presentation data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        presentation_data = json.load(f)
    
    # List to store video clips
    video_clips = []
    
    # Process each slide
    for slide in presentation_data.get('slides', []):
        if 'image_path' in slide and 'audio_path' in slide:
            # Load the audio to get its duration
            audio = AudioFileClip(slide['audio_path'])
            duration = audio.duration
            
            # Create a video clip from the image
            image = ImageClip(slide['image_path'])
            
            # Set the duration of the image to match the audio
            video_clip = image.set_duration(duration)
            
            # Add the audio to the clip
            video_clip = video_clip.set_audio(audio)
            
            video_clips.append(video_clip)
    
    # Concatenate all clips
    final_video = concatenate_videoclips(video_clips)
    
    # Write the final video
    final_video.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio_codec='aac'
    )
    
    # Close all clips to free up resources
    for clip in video_clips:
        clip.close()
    final_video.close()

if __name__ == "__main__":
    create_presentation_video("presentation_results.json") 