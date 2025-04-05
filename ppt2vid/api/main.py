from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import uuid
import json
from typing import Dict

from ppt2vid.config.groq_config import GroqConfig
from ppt2vid.core.ppt_converter import PPTConverter
from ppt2vid.core.ai_service import AIService
from ppt2vid.api.models import PresentationResponse, ErrorResponse, ProcessingStatus

app = FastAPI(
    title="PPT to Video Script API",
    description="API for converting PowerPoint presentations to video scripts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for processing status
processing_status: Dict[str, ProcessingStatus] = {}

@app.post("/upload", response_model=ProcessingStatus)
async def upload_presentation(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> JSONResponse:
    """Upload a PowerPoint presentation for processing."""
    if not file.filename.endswith(('.ppt', '.pptx')):
        raise HTTPException(
            status_code=400,
            detail="Only PowerPoint files (.ppt, .pptx) are supported"
        )

    # Create a unique processing ID
    processing_id = str(uuid.uuid4())
    
    # Create temporary directory for processing
    temp_dir = Path(f"temp/{processing_id}")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the uploaded file
    file_path = temp_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Initialize processing status
    status = ProcessingStatus(
        status="uploaded",
        message="File uploaded successfully",
        progress=0.0
    )
    processing_status[processing_id] = status
    
    # Add background task for processing
    background_tasks.add_task(process_presentation, processing_id, file_path)
    
    # Return response with processing ID in headers
    return JSONResponse(
        content=status.dict(),
        headers={"Location": f"/status/{processing_id}"}
    )

@app.get("/status/{processing_id}", response_model=ProcessingStatus)
async def get_status(processing_id: str) -> ProcessingStatus:
    """Get the processing status of a presentation."""
    if processing_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail="Processing ID not found"
        )
    return processing_status[processing_id]

@app.get("/result/{processing_id}", response_model=PresentationResponse)
async def get_result(processing_id: str) -> PresentationResponse:
    """Get the processed presentation result."""
    if processing_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail="Processing ID not found"
        )
    
    status = processing_status[processing_id]
    if status.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Processing not completed yet"
        )
    
    # Read the result file
    result_file = Path(f"temp/{processing_id}/presentation_script.json")
    if not result_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Result file not found"
        )
    
    with result_file.open() as f:
        result_data = json.load(f)
    
    return PresentationResponse(**result_data)

async def process_presentation(processing_id: str, file_path: Path) -> None:
    """Process the presentation in the background."""
    try:
        # Update status to processing
        processing_status[processing_id] = ProcessingStatus(
            status="processing",
            message="Processing presentation",
            progress=0.0
        )
        
        # Initialize services
        config = GroqConfig()
        ppt_converter = PPTConverter(Path(f"temp/{processing_id}"))
        ai_service = AIService(config)
        
        # Convert PPT to images
        presentation = ppt_converter.convert_to_images(file_path)
        
        # Update status with total slides
        processing_status[processing_id] = ProcessingStatus(
            status="processing",
            message="Processing slides",
            progress=0.0,
            total_slides=len(presentation.slides)
        )
        
        # Process each slide
        for idx, slide in enumerate(presentation.slides):
            # Update progress
            progress = (idx + 1) / len(presentation.slides)
            processing_status[processing_id] = ProcessingStatus(
                status="processing",
                message=f"Processing slide {idx + 1} of {len(presentation.slides)}",
                progress=progress,
                current_slide=idx + 1,
                total_slides=len(presentation.slides)
            )
            
            # Extract text using OCR
            slide.ocr_text = ai_service.extract_text(slide.image_path)
            
            # Generate image summary
            slide.summary = ai_service.generate_summary(slide.image_path)
            
            # Generate script
            slide.script = ai_service.generate_script(slide)
        
        # Save results
        result_file = Path(f"temp/{processing_id}/presentation_script.json")
        with result_file.open("w") as f:
            json.dump(presentation.to_dict(), f, indent=2)
        
        # Update status to completed
        processing_status[processing_id] = ProcessingStatus(
            status="completed",
            message="Processing completed successfully",
            progress=1.0
        )
        
    except Exception as e:
        # Update status to error
        processing_status[processing_id] = ProcessingStatus(
            status="error",
            message=str(e),
            progress=0.0
        ) 