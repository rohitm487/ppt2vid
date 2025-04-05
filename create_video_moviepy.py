import json
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import numpy as np

def create_presentation_video(json_file_path, output_path="presentation.mp4"):
    """
    Create a video from slides and audio files using moviepy.
    Each slide is shown for the duration of its corresponding audio narration.
    """
    # Load the presentation data
    with open(json_file_path, 'r') as f:
        presentation_data = json.load(f)
    
    # Create video clips for each slide
    clips = []
    for slide in presentation_data['slides']:  # Access slides from the 'slides' key
        if 'image_path' in slide and 'audio_path' in slide:
            # Create image clip
            image_clip = ImageClip(slide['image_path'])
            
            # Load audio and get its duration
            audio_clip = AudioFileClip(slide['audio_path'])
            
            # Set the duration of the image clip to match the audio
            image_clip = image_clip.set_duration(audio_clip.duration)
            
            # Add audio to the clip
            video_clip = image_clip.set_audio(audio_clip)
            
            clips.append(video_clip)
    
    if not clips:
        raise ValueError("No valid slides found in the presentation data")
    
    # Concatenate all clips
    final_clip = concatenate_videoclips(clips)
    
    # Write the result
    final_clip.write_videofile(output_path, fps=24, codec='libx264')
    
    # Close all clips to free up resources
    for clip in clips:
        clip.close()
    final_clip.close()

if __name__ == "__main__":
    try:
        create_presentation_video("presentation_results.json")
        print("Video created successfully!")
    except Exception as e:
        print(f"Error creating video: {str(e)}") 