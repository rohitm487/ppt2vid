import gradio as gr
import json
from pathlib import Path
import os
from typing import Dict, Any
import requests
from ppt2vid.core.tts_converter import convert_text_to_speech
from ppt2vid.core.video_creator import create_presentation_video

def load_presentation(json_path: str) -> Dict[str, Any]:
    """Load presentation data from JSON file."""
    with open(json_path, 'r') as f:
        return json.load(f)

def save_presentation(data: Dict[str, Any], json_path: str) -> None:
    """Save presentation data to JSON file."""
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

def update_script(presentation_data: Dict[str, Any], slide_idx: int, new_script: str) -> Dict[str, Any]:
    """Update the script for a specific slide."""
    presentation_data['slides'][slide_idx]['script'] = new_script
    return presentation_data

def generate_audio_files(presentation_data: Dict[str, Any], processing_id: str) -> str:
    """Generate audio files for all slides."""
    try:
        for i, slide in enumerate(presentation_data['slides']):
            audio_path = f"temp/{processing_id}/audio/slide_{i+1}.aiff"
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            convert_text_to_speech(slide['script'], audio_path)
            slide['audio_path'] = audio_path
        return "Audio files generated successfully!"
    except Exception as e:
        return f"Error generating audio: {str(e)}"

def create_video(presentation_data: Dict[str, Any], processing_id: str) -> str:
    """Create video from slides and audio."""
    try:
        # Save current state of presentation data
        json_path = f"temp/{processing_id}/presentation_results.json"
        save_presentation(presentation_data, json_path)
        
        # Create video
        output_path = f"temp/{processing_id}/presentation.mp4"
        create_presentation_video(json_path, output_path)
        return f"Video created successfully! Path: {output_path}"
    except Exception as e:
        return f"Error creating video: {str(e)}"

class GradioInterface:
    def __init__(self):
        self.interface = self.create_interface()
    
    def load_slide(self, presentation: Dict, slide_idx: int):
        """Load a specific slide's data."""
        if not presentation or 'slides' not in presentation:
            return None, "", "No presentation loaded"
        
        slides = presentation['slides']
        if not slides or slide_idx >= len(slides):
            return None, "", "Invalid slide index"
        
        slide = slides[slide_idx]
        return (
            slide['image_path'],
            slide.get('script', ''),
            f"Slide {slide_idx + 1}/{len(slides)}"
        )
    
    def update_current_script(self, presentation: Dict, slide_idx: int, new_script: str):
        """Update the script for the current slide."""
        if presentation and 'slides' in presentation:
            presentation = update_script(presentation, slide_idx, new_script)
            return presentation, "Script updated successfully!"
        return presentation, "Error: No presentation loaded"
    
    def create_interface(self):
        """Create the Gradio interface."""
        with gr.Blocks() as interface:
            gr.Markdown("# Presentation Editor")
            
            # State variables
            presentation_data = gr.State(None)
            processing_id = gr.State(None)
            current_slide = gr.State(0)
            
            with gr.Row():
                # Left column for slide navigation and info
                with gr.Column(scale=1):
                    slide_info = gr.Markdown("Slide 1/1")
                    prev_btn = gr.Button("Previous Slide")
                    next_btn = gr.Button("Next Slide")
                
                # Right column for slide content and editing
                with gr.Column(scale=2):
                    image_display = gr.Image(label="Slide Preview")
                    script_input = gr.Textbox(
                        label="Script",
                        lines=10,
                        placeholder="Enter script for this slide..."
                    )
                    update_btn = gr.Button("Update Script")
            
            with gr.Row():
                generate_audio_btn = gr.Button("Generate Audio")
                create_video_btn = gr.Button("Create Video")
            
            output_message = gr.Textbox(label="Status")
            
            # Event handlers
            prev_btn.click(
                fn=lambda idx: max(0, idx - 1),
                inputs=[current_slide],
                outputs=[current_slide]
            ).then(
                fn=self.load_slide,
                inputs=[presentation_data, current_slide],
                outputs=[image_display, script_input, slide_info]
            )
            
            next_btn.click(
                fn=lambda idx, pres: min(len(pres['slides']) - 1 if pres else 0, idx + 1),
                inputs=[current_slide, presentation_data],
                outputs=[current_slide]
            ).then(
                fn=self.load_slide,
                inputs=[presentation_data, current_slide],
                outputs=[image_display, script_input, slide_info]
            )
            
            update_btn.click(
                fn=self.update_current_script,
                inputs=[presentation_data, current_slide, script_input],
                outputs=[presentation_data, output_message]
            )
            
            generate_audio_btn.click(
                fn=generate_audio_files,
                inputs=[presentation_data, processing_id],
                outputs=[output_message]
            )
            
            create_video_btn.click(
                fn=create_video,
                inputs=[presentation_data, processing_id],
                outputs=[output_message]
            )
        
        return interface
    
    def mount_in_app(self, app):
        """Mount the Gradio interface in a FastAPI app."""
        return gr.mount_gradio_app(app, self.interface, path="/") 