from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request, Depends, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import uuid
import json
from typing import Dict, List
import os
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import time

from ppt2vid.config.groq_config import GroqConfig
from ppt2vid.core.image_processor import ImageProcessor
from ppt2vid.core.ai_service import AIService
from ppt2vid.core.tts_converter import convert_text_to_speech
from ppt2vid.database import engine, get_db
from ppt2vid.models.user import Base, User, UserRole, SubscriptionTier
from ppt2vid.auth import get_current_user, auth_config, create_access_token
from ppt2vid.auth.rbac import check_user_limits, require_feature, require_role, get_user_features
from ppt2vid.api.schemas import (
    UserResponse, UserFeatures, MessageResponse, Token,
    ProcessingStatus, PresentationResponse, ErrorResponse, UpgradeRequest
)
from ppt2vid.core.create_video_moviepy import create_presentation_video

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Image to Video Script API",
    description="API for converting image slides to video scripts",
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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount temp directory for slide images
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

# Templates
templates = Jinja2Templates(directory="templates")

# Global storage for processing status
processing_status: Dict[str, ProcessingStatus] = {}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the main page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "client_id": auth_config.google_client_id
        }
    )

@app.get("/api/user/features", response_model=UserFeatures)
async def get_user_features_endpoint(current_user: User = Depends(get_current_user)) -> UserFeatures:
    """Get user's features and limits based on their subscription tier."""
    try:
        features = get_user_features(current_user)
        return UserFeatures(**features)
    except Exception as e:
        print(f"Error getting user features: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user features: {str(e)}"
        )

@app.post("/upload", response_model=ProcessingStatus)
async def upload_slides(
    files: list[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user)
) -> JSONResponse:
    """Upload numbered image files for processing."""
    # Check user limits
    limits = check_user_limits(current_user, num_slides=len(files))
    
    # Create a unique processing ID
    processing_id = str(uuid.uuid4())
    
    # Create temporary directory for processing
    temp_dir = Path(f"temp/{processing_id}")
    slides_dir = temp_dir / "slides"
    slides_dir.mkdir(parents=True, exist_ok=True)
    
    # Allowed image formats
    ALLOWED_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    
    # Save all uploaded files
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Only image files ({', '.join(ALLOWED_FORMATS)}) are supported"
            )
        
        # Save the uploaded file
        file_path = slides_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    
    # Initialize processing status
    status = ProcessingStatus(
        status="uploaded",
        message="Image files uploaded successfully",
        progress=0.0
    )
    processing_status[processing_id] = status
    
    # Add background task for processing
    background_tasks.add_task(process_slides, processing_id)
    
    # Update user video count
    db = next(get_db())
    current_user.videos_generated += 1
    db.commit()
    
    return JSONResponse(
        content={
            "processing_id": processing_id,
            "status": status.status,
            "message": status.message,
            "progress": status.progress,
            "features": get_user_features(current_user)
        },
        headers={"Location": f"/status/{processing_id}"}
    )

@app.get("/status/{processing_id}", response_model=ProcessingStatus)
async def get_status(processing_id: str) -> ProcessingStatus:
    """Get the processing status."""
    if processing_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail="Processing ID not found"
        )
    return processing_status[processing_id]

@app.get("/result/{processing_id}", response_model=PresentationResponse)
async def get_result(processing_id: str) -> PresentationResponse:
    """Get the processed result."""
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

@app.post("/video/{processing_id}", response_model=MessageResponse)
async def create_video(
    processing_id: str,
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Create a video from the processed slides."""
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
    
    try:
        # Ensure temp directory exists
        temp_dir = Path(f"temp/{processing_id}")
        if not temp_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Processing directory not found: {temp_dir}"
            )

        # Load data
        result_file = temp_dir / "presentation_script.json"
        if not result_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Result file not found: {result_file}"
            )
        
        # Get user features and limits
        features = get_user_features(current_user)
        
        # Create audio directory
        audio_dir = temp_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        
        # Generate audio files
        total_duration = 0
        with result_file.open() as f:
            data = json.load(f)
            
        if not data.get('slides'):
            raise HTTPException(
                status_code=400,
                detail="No slides found in presentation data"
            )
            
        for i, slide in enumerate(data['slides']):
            if not slide.get('script'):
                raise HTTPException(
                    status_code=400,
                    detail=f"No script found for slide {i+1}"
                )
                
            audio_path = audio_dir / f"slide_{i+1}.aiff"
            try:
                convert_text_to_speech(slide['script'], str(audio_path))
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate audio for slide {i+1}: {str(e)}"
                )
                
            slide['audio_path'] = str(audio_path)
            
            # Calculate duration
            try:
                audio_clip = AudioFileClip(str(audio_path))
                total_duration += audio_clip.duration
                audio_clip.close()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to process audio for slide {i+1}: {str(e)}"
                )
            
            # Check duration limit
            if total_duration > features['limits']['max_video_duration']:
                raise HTTPException(
                    status_code=403,
                    detail=f"Video duration exceeds the limit for your subscription tier ({features['limits']['max_video_duration']} seconds)"
                )
        
        # Save updated data with audio paths
        with result_file.open('w') as f:
            json.dump(data, f, indent=2)
        
        # Create video using the standalone function
        output_path = temp_dir / "video.mp4"
        try:
            create_presentation_video(str(result_file), str(output_path))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create video: {str(e)}"
            )
        
        if not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Video file was not created successfully"
            )
        
        return MessageResponse(
            message="Video created successfully",
            video_path=f"/temp/{processing_id}/video.mp4"
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error in video creation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create video: {str(e)}"
        )

@app.get("/scripts/{processing_id}", response_model=MessageResponse)
async def get_scripts(processing_id: str) -> MessageResponse:
    """Get the generated scripts."""
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
        data = json.load(f)
    
    # Extract scripts from slides
    scripts = [slide.get('script', '') for slide in data.get('slides', [])]
    
    return MessageResponse(message="Scripts retrieved successfully", scripts=scripts)

@app.put("/scripts/{processing_id}", response_model=MessageResponse)
@require_feature("custom_scripts")
async def update_presentation_scripts(
    processing_id: str,
    data: dict,
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Update the presentation scripts. Requires custom_scripts feature."""
    if processing_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail="Processing ID not found"
        )
    
    try:
        # Save updated data
        result_file = Path(f"temp/{processing_id}/presentation_script.json")
        with result_file.open("w") as f:
            json.dump(data, f, indent=2)
        
        return MessageResponse(message="Scripts updated successfully")
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

async def process_slides(processing_id: str) -> None:
    """Process the uploaded images in the background."""
    try:
        # Update status to processing
        processing_status[processing_id] = ProcessingStatus(
            status="processing",
            message="Processing uploaded images",
            progress=0.0
        )
        
        # Initialize services
        config = GroqConfig()
        image_processor = ImageProcessor(Path(f"temp/{processing_id}"))
        ai_service = AIService(config)
        
        # Process the numbered images
        presentation = image_processor.process_images()
        
        # Update status for OCR phase
        processing_status[processing_id] = ProcessingStatus(
            status="processing",
            message="Performing OCR on slides",
            progress=0.2,
            total_slides=len(presentation.slides)
        )
        
        # Process each slide - OCR and Summarization
        for idx, slide in enumerate(presentation.slides):
            # Update progress for OCR
            progress = 0.2 + (idx / len(presentation.slides)) * 0.6  # OCR phase is 60% of total
            processing_status[processing_id] = ProcessingStatus(
                status="processing",
                message=f"Processing slide {idx + 1}/{len(presentation.slides)} - OCR",
                progress=progress,
                total_slides=len(presentation.slides),
                current_slide=idx + 1
            )
            
            # Perform OCR on the slide image
            slide.ocr_text = ai_service.extract_text(slide.image_path)
            
            # Update progress for summarization
            progress = 0.8 + (idx / len(presentation.slides)) * 0.2  # Summarization is 20% of total
            processing_status[processing_id] = ProcessingStatus(
                status="processing",
                message=f"Processing slide {idx + 1}/{len(presentation.slides)} - Generating script",
                progress=progress,
                total_slides=len(presentation.slides),
                current_slide=idx + 1
            )
            
            # Generate summary and script
            slide.summary = ai_service.generate_summary(slide.image_path)
            slide.script = ai_service.generate_script(slide.ocr_text)
            
            # Save intermediate results after each slide
            result_file = Path(f"temp/{processing_id}/presentation_script.json")
            with result_file.open('w') as f:
                json.dump(presentation.to_dict(), f, indent=2)
        
        # Update status to completed
        processing_status[processing_id] = ProcessingStatus(
            status="completed",
            message="Processing completed",
            progress=1.0,
            total_slides=len(presentation.slides)
        )
        
    except Exception as e:
        # Update status to error
        processing_status[processing_id] = ProcessingStatus(
            status="error",
            message=str(e),
            progress=0.0
        )

@app.get("/api/user/me", response_model=UserResponse)
async def get_user_info(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get current user information."""
    return UserResponse.from_orm(current_user)

@app.post("/api/user/upgrade/{tier}", response_model=MessageResponse)
async def upgrade_subscription(
    tier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    try:
        new_tier = SubscriptionTier(tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
    
    current_user.subscription_tier = new_tier
    db.commit()
    return MessageResponse(message=f"Subscription upgraded to {tier}")

@app.post("/api/admin/set-role", response_model=MessageResponse)
async def set_user_role(
    email: str,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    if current_user.role != UserRole.SUPERUSER:
        raise HTTPException(status_code=403, detail="Superuser role required")
        
    try:
        new_role = UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = new_role
    db.commit()
    return MessageResponse(message=f"Role updated to {role} for user {email}")

@app.post("/api/auth/google", response_model=Token)
async def google_auth(request: Request, db: Session = Depends(get_db)) -> Token:
    """Handle Google Sign-In."""
    try:
        # Get the request body
        data = await request.json()
        token = data.get("credential")
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        # Verify the token with Google
        try:
            id_info = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                auth_config.google_client_id
            )

            # Check if the token is valid
            if id_info['aud'] != auth_config.google_client_id:
                raise HTTPException(status_code=401, detail="Invalid token audience")

            # Get or create user
            user = db.query(User).filter(User.email == id_info['email']).first()
            if not user:
                user = User(
                    email=id_info['email'],
                    name=id_info.get('name'),
                    picture=id_info.get('picture'),
                    role=UserRole.BASIC,
                    subscription_tier=SubscriptionTier.FREE,
                    videos_generated=0
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # Create access token
            access_token = create_access_token(
                data={"sub": user.email},
                expires_delta=timedelta(days=7)
            )

            return Token(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse.from_orm(user)
            )

        except ValueError as e:
            print(f"Token verification error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")

    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/users", response_model=List[UserResponse])
@require_role(UserRole.SUPERUSER)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """List all users. Requires superuser role."""
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.from_orm(u) for u in users]

@app.put("/admin/users/{user_id}/role", response_model=MessageResponse)
@require_role(UserRole.SUPERUSER)
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Update a user's role. Requires superuser role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role
    db.commit()
    
    return MessageResponse(
        message=f"User role updated successfully to {role.value}"
    )

@app.put("/admin/users/{user_id}/subscription", response_model=MessageResponse)
@require_role(UserRole.SUPERUSER)
async def update_user_subscription(
    user_id: int,
    subscription_tier: SubscriptionTier,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Update a user's subscription tier. Requires superuser role."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.subscription_tier = subscription_tier
    db.commit()
    
    return MessageResponse(
        message=f"User subscription updated successfully to {subscription_tier.value}"
    )

@app.post("/api/user/request-upgrade", response_model=MessageResponse)
async def request_upgrade(
    payment_method: str = Form(...),
    email: str = Form(...),
    transaction_id: str = Form(...),
    transaction_image: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Handle subscription upgrade request."""
    try:
        # Create requests directory if it doesn't exist
        requests_dir = Path("upgrade_requests")
        requests_dir.mkdir(exist_ok=True)
        
        # Create a unique file for this request
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        request_file = requests_dir / f"upgrade_request_{timestamp}_{current_user.email}.json"
        
        # Save request data
        request_data = {
            "timestamp": timestamp,
            "user_email": current_user.email,
            "user_name": current_user.name,
            "current_plan": current_user.subscription_tier.value,
            "payment_method": payment_method,
            "contact_email": email,
            "transaction_id": transaction_id
        }
        
        # Save transaction image if provided
        if transaction_image:
            # Validate file size (1MB limit)
            contents = await transaction_image.read()
            if len(contents) > 1024 * 1024:  # 1MB
                raise HTTPException(
                    status_code=400,
                    detail="Transaction image must be less than 1MB"
                )
            
            # Save the image
            image_path = requests_dir / f"transaction_image_{timestamp}_{current_user.email}.png"
            with image_path.open("wb") as f:
                f.write(contents)
            request_data["transaction_image_path"] = str(image_path)
        
        with request_file.open('w') as f:
            json.dump(request_data, f, indent=2)
        
        # Send notification to admin email if configured
        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email:
            try:
                # Create the email message
                msg = MIMEMultipart()
                msg['From'] = os.getenv('EMAIL_FROM', 'noreply@ppt2vid.com')
                msg['To'] = admin_email
                msg['Subject'] = f'New Upgrade Request - {current_user.email}'

                # Email body
                body = f"""
                New Upgrade Request

                User Details:
                - Email: {current_user.email}
                - Name: {current_user.name}
                - Current Plan: {current_user.subscription_tier.value}
                - Contact Email: {email}
                - Payment Method: {payment_method}
                - Transaction ID: {transaction_id}
                """

                msg.attach(MIMEText(body, 'plain'))

                # Attach transaction image if provided
                if transaction_image and "transaction_image_path" in request_data:
                    with open(request_data["transaction_image_path"], 'rb') as f:
                        img = MIMEImage(f.read())
                        img.add_header('Content-Disposition', 'attachment', filename=f'transaction_{timestamp}.png')
                        msg.attach(img)

                # Send email using SMTP if configured
                if os.getenv('EMAIL_USERNAME') and os.getenv('EMAIL_PASSWORD'):
                    with smtplib.SMTP('smtp.gmail.com', 587) as server:
                        server.starttls()
                        server.login(
                            os.getenv('EMAIL_USERNAME'),
                            os.getenv('EMAIL_PASSWORD')
                        )
                        server.send_message(msg)

            except Exception as e:
                print(f"Failed to send email notification: {str(e)}")
                # Continue execution even if email fails
        
        return MessageResponse(
            message="Upgrade request received successfully. We will contact you shortly."
        )

    except Exception as e:
        print(f"Error processing upgrade request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process upgrade request. Please try again later."
        )

@app.post("/api/payments/create-order", response_model=dict)
async def create_payment_order(
    current_user: User = Depends(get_current_user)
) -> dict:
    """Create a simulated Razorpay order for premium upgrade."""
    try:
        # Simulate Razorpay order creation
        amount = 149900  # Rs. 1,499.00
        timestamp = int(time.time())
        order_id = f"order_{timestamp}_{current_user.id}"
        
        order_data = {
            "id": order_id,
            "entity": "order",
            "amount": amount,
            "amount_paid": 0,
            "amount_due": amount,
            "currency": "INR",
            "receipt": f"receipt_{timestamp}",
            "status": "created",
            "attempts": 0,
            "notes": {
                "user_id": str(current_user.id),
                "user_email": current_user.email
            },
            "created_at": timestamp
        }
        
        return order_data
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {
                "code": "BAD_REQUEST_ERROR",
                "description": str(e),
                "source": "business",
                "step": "payment_initiation",
                "reason": "order_creation_failed"
            }}
        )

@app.post("/api/payments/verify-payment")
async def verify_payment(
    payment_details: dict,
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """Verify payment and upgrade user to premium."""
    try:
        # In a real implementation, you would verify the payment with Razorpay here
        # For simulation, we'll just check if payment_details contains required fields
        if not all(key in payment_details for key in ["orderId", "paymentId", "signature"]):
            raise ValueError("Invalid payment details")
            
        # Update user's subscription to premium
        current_user.subscription_tier = SubscriptionTier.PREMIUM
        db.commit()
        
        return MessageResponse(message="Payment successful! Your account has been upgraded to Premium.")
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {
                "code": "PAYMENT_VERIFICATION_FAILED",
                "description": str(e),
                "source": "business",
                "step": "payment_verification",
                "reason": "verification_failed"
            }}
        ) 