from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import os
import json
import logging
from typing import List, Optional
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class PredictionResponse(BaseModel):
    disease: str = Field(..., description="Detected disease name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    solution: str = Field(..., description="Treatment solution")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    labels_count: int
    solutions_count: int
    uptime_seconds: float

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

app = FastAPI(
    title="FloraGuard AI Backend",
    description="Plant Disease Detection API using TensorFlow Lite",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit default
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
INPUT_SIZE = 224  # Updated to match model expectation

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Check for local assets directory (Docker/Deployment)
LOCAL_ASSETS_DIR = os.path.join(BASE_DIR, "assets")

if os.path.exists(LOCAL_ASSETS_DIR) and os.path.exists(os.path.join(LOCAL_ASSETS_DIR, "model.tflite")):
    logger.info(f"Using local assets directory: {LOCAL_ASSETS_DIR}")
    MODEL_PATH = os.path.join(LOCAL_ASSETS_DIR, "model.tflite")
    LABELS_PATH = os.path.join(LOCAL_ASSETS_DIR, "labels.txt")
    DATA_PATH = os.path.join(LOCAL_ASSETS_DIR, "data.json")
else:
    # Fallback to project structure (Local Development)
    logger.info("Using project structure paths")
    ASSETS_DIR = os.path.join(PROJECT_ROOT, "android_app", "app", "src", "main", "assets")
    MODEL_PATH = os.path.join(ASSETS_DIR, "model.tflite")
    LABELS_PATH = os.path.join(ASSETS_DIR, "labels.txt")
    DATA_PATH = os.path.join(PROJECT_ROOT, "web_app", "data.json")

# Global variables for model and data
interpreter = None
labels = []
solutions = {}
start_time = time.time()

@app.on_event("startup")
async def load_resources():
    global interpreter, labels, solutions
    try:
        logger.info("Loading backend resources...")
        
        # Validate file paths
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        if not os.path.exists(LABELS_PATH):
            raise FileNotFoundError(f"Labels file not found: {LABELS_PATH}")
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
        
        # Load TFLite Model
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        logger.info("TensorFlow Lite model loaded successfully")
        
        # Load Labels
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            labels = [line.strip() for line in f.readlines()]
        logger.info(f"Loaded {len(labels)} labels")
            
        # Load Solutions
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            solutions = json.load(f)
        logger.info(f"Loaded {len(solutions)} disease solutions")
            
        logger.info("Backend resources loaded successfully")
    except Exception as e:
        logger.error(f"Error loading resources: {e}")
        raise RuntimeError(f"Failed to initialize backend: {e}")

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size (this is approximate, actual size checked after reading)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

def preprocess_image(image: Image.Image) -> np.ndarray:
    """Preprocess image for model inference"""
    try:
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image
        image = image.resize((INPUT_SIZE, INPUT_SIZE), Image.Resampling.LANCZOS)
        
        # Convert to numpy array and normalize
        image_array = np.array(image, dtype=np.float32)
        image_array = image_array / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process image"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with detailed status"""
    return HealthResponse(
        status="healthy" if interpreter is not None else "unhealthy",
        model_loaded=interpreter is not None,
        labels_count=len(labels),
        solutions_count=len(solutions),
        uptime_seconds=time.time() - start_time
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_disease(file: UploadFile = File(...)):
    """Predict plant disease from uploaded image"""
    start_time_request = time.time()
    
    if not interpreter:
        logger.error("Model not loaded")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model not loaded"
        )
    
    try:
        # Validate file
        validate_image_file(file)
        
        # Read and validate file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Open and preprocess image
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        processed_image = preprocess_image(image)
        
        # Get model input/output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        # Set input tensor
        interpreter.set_tensor(input_details[0]['index'], processed_image)
        
        # Run inference
        interpreter.invoke()
        
        # Get prediction
        predictions = interpreter.get_tensor(output_details[0]['index'])[0]
        
        # Get top prediction
        top_prediction_idx = np.argmax(predictions)
        confidence = float(predictions[top_prediction_idx])
        
        if top_prediction_idx < len(labels):
            disease_name = labels[top_prediction_idx]
        else:
            logger.warning(f"Prediction index {top_prediction_idx} out of range for labels")
            disease_name = "unknown"
        
        # Get solution with better key matching
        # Convert model output format to solution key format
        solution_key = disease_name.replace("___", " ").replace("_", " ").lower().strip()
        solution = solutions.get(solution_key, "No specific solution available. Please consult with a plant pathologist for proper diagnosis and treatment.")
        
        processing_time = (time.time() - start_time_request) * 1000
        
        logger.info(f"Prediction: {disease_name} (confidence: {confidence:.3f}, time: {processing_time:.1f}ms)")
        
        return PredictionResponse(
            disease=disease_name,
            confidence=confidence,
            solution=solution,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during prediction"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=f"HTTP {exc.status_code}"
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
