# Deployment Trigger: Force Vercel to pick up Python 3.9 config
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
except ImportError:
    import tflite_runtime.interpreter as tflite
    Interpreter = tflite.Interpreter
import numpy as np
from PIL import Image
import io
import os
import json
import logging
from typing import List, Optional, Dict
import time
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import redis
import hashlib
import json as json_lib
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables from .env file
load_dotenv()

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

# Global variables for model and data
interpreter = None
gemini_model = None
labels = []
solutions = {}
start_time = time.time()

# Redis connection
redis_client = None
slack_client = None

def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        redis_db = int(os.getenv("REDIS_DB", 0))
        redis_password = os.getenv("REDIS_PASSWORD", None)
        
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password if redis_password else None,
            decode_responses=True
        )
        
        # Test connection
        redis_client.ping()
        logger.info("[OK] Redis connected successfully")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None
        return False

def init_slack():
    """Initialize Slack client"""
    global slack_client
    try:
        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if slack_token:
            slack_client = WebClient(token=slack_token)
            # Test connection
            slack_client.auth_test()
            logger.info("[OK] Slack client initialized successfully")
            return True
        else:
            logger.info("[INFO] Slack token not provided, notifications disabled")
            return False
    except Exception as e:
        logger.warning(f"[WARNING] Slack initialization failed: {e}")
        slack_client = None
        return False

def get_image_hash(image_bytes: bytes) -> str:
    """Generate a hash for image caching"""
    return hashlib.md5(image_bytes).hexdigest()

def get_cached_prediction(image_hash: str) -> Optional[dict]:
    """Get cached prediction result"""
    if not redis_client:
        return None
    
    try:
        cached_result = redis_client.get(f"prediction:{image_hash}")
        if cached_result:
            logger.info(f"🚀 Cache HIT for image hash: {image_hash[:8]}...")
            return json_lib.loads(cached_result)
    except Exception as e:
        logger.error(f"Cache read error: {e}")
    
    return None

def cache_prediction(image_hash: str, prediction_result: dict, ttl: int = 3600):
    """Cache prediction result (TTL in seconds, default 1 hour)"""
    if not redis_client:
        return
    
    try:
        redis_client.setex(
            f"prediction:{image_hash}",
            ttl,
            json_lib.dumps(prediction_result)
        )
        logger.info(f"💾 Cached prediction for hash: {image_hash[:8]}...")
    except Exception as e:
        logger.error(f"Cache write error: {e}")

def send_slack_alert(disease: str, confidence: float, layer: str, image_hash: str = None):
    """Send Slack notification for disease detection"""
    if not slack_client:
        return
    
    try:
        channel = os.getenv("SLACK_CHANNEL", "#plant-alerts")
        
        # Determine alert level
        if confidence < 0.5:
            alert_emoji = "⚠️"
            alert_level = "LOW CONFIDENCE"
        elif "emergency" in disease.lower() or confidence > 0.9:
            alert_emoji = "🚨"
            alert_level = "HIGH PRIORITY"
        else:
            alert_emoji = "🔍"
            alert_level = "DETECTED"
        
        message = f"""
{alert_emoji} *Plant Disease {alert_level}*

🦠 *Disease:* {disease}
📊 *Confidence:* {confidence:.1%}
🔬 *Analysis Layer:* {layer}
⏰ *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{f"🔗 *Image Hash:* {image_hash[:8]}..." if image_hash else ""}

_Automated alert from FloraGuard AI_
        """
        
        slack_client.chat_postMessage(
            channel=channel,
            text=message,
            username="FloraGuard AI",
            icon_emoji=":herb:"
        )
        
        logger.info(f"📤 Slack alert sent for: {disease}")
        
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
    except Exception as e:
        logger.error(f"Slack notification error: {e}")

def send_slack_reminder(medication: str, dosage: str, frequency: str, disease: str):
    """Send Slack reminder for medication"""
    if not slack_client:
        return
    
    try:
        channel = os.getenv("SLACK_CHANNEL", "#plant-alerts")
        
        message = f"""
🔔 *Medication Reminder*

💊 *Medication:* {medication}
📏 *Dosage:* {dosage}
⏰ *Frequency:* {frequency}
🦠 *For Disease:* {disease}
📅 *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

_Don't forget your plant treatment! 🌱_
        """
        
        slack_client.chat_postMessage(
            channel=channel,
            text=message,
            username="FloraGuard Reminder",
            icon_emoji=":alarm_clock:"
        )
        
        logger.info(f"📤 Slack reminder sent for: {medication}")
        
    except SlackApiError as e:
        logger.error(f"Slack API error: {e.response['error']}")
    except Exception as e:
        logger.error(f"Slack reminder error: {e}")

class TreatmentStage(BaseModel):
    name: str
    description: str
    components: List[str]
    medications: List[str]

class Medication(BaseModel):
    name: str
    dosage: str
    frequency: str
    side_effects: str

class EmergencyInfo(BaseModel):
    action: str
    signs: List[str]

class RecoveryInfo(BaseModel):
    timeline: List[str]
    success_rate: str

class DiseaseDetail(BaseModel):
    name: str
    causes: Dict[str, str]
    prevention: Dict[str, List[str]]
    treatment: Dict[str, List[TreatmentStage]]
    medications: List[Medication]
    emergency: EmergencyInfo
    recovery: RecoveryInfo

# Pydantic models for request/response validation
class PredictionResponse(BaseModel):
    disease: str = Field(..., description="Detected disease name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    solution: str = Field(..., description="Treatment solution")
    layer: str = Field(..., description="The AI layer that produced this result (Layer 1 or Layer 2)")
    details: Optional[DiseaseDetail] = Field(None, description="Enriched disease details from Gemini")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cached: bool = Field(default=False, description="Whether result was served from cache")

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
    global interpreter, labels, solutions, gemini_model
    try:
        logger.info("Loading backend resources...")
        
        # Initialize Redis and Slack
        init_redis()
        init_slack()
        
        # Configure Gemini
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if GEMINI_API_KEY:
            logger.info(f"Configuring Gemini with key starting with {GEMINI_API_KEY[:5]}...")
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Lightweight Model Selection Strategy - Free Tier Optimized
            candidate_models = [
                'gemini-flash-latest',  # Most stable free tier model
                'gemini-2.0-flash-lite',  # Lite version for speed
                'gemini-2.0-flash-lite-001',
                'gemini-2.5-flash',  # Latest but may have quota limits
                'gemini-2.0-flash'
            ]
            
            # Quick connection test without consuming quota
            active_model = None
            for model_name in candidate_models:
                try:
                    logger.info(f"Testing model: {model_name}...")
                    # Just initialize the model without making a request
                    test_model = genai.GenerativeModel(model_name)
                    active_model = test_model
                    logger.info(f"[OK] Model {model_name} initialized successfully")
                    break
                except Exception as e:
                    logger.warning(f"[FAIL] Failed to initialize {model_name}: {e}")
            
            if active_model:
                gemini_model = active_model
                logger.info("Gemini Layer 2 fallback configured successfully (quota-aware).")
            else:
                logger.error("CRITICAL: All Gemini models failed to initialize. Layer 2 disabled.")
                gemini_model = None
        else:
            logger.warning("GEMINI_API_KEY not found. Layer 2 fallback disabled.")
            gemini_model = None
        
        # Validate file paths
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        if not os.path.exists(LABELS_PATH):
            raise FileNotFoundError(f"Labels file not found: {LABELS_PATH}")
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
        
        # Load TFLite Model
        interpreter = Interpreter(model_path=MODEL_PATH)
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
    """Preprocess image for model inference - optimized for speed"""
    try:
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize image with faster resampling method
        image = image.resize((INPUT_SIZE, INPUT_SIZE), Image.Resampling.BILINEAR)  # Faster than LANCZOS
        
        # Convert to numpy array and normalize - optimized
        image_array = np.array(image, dtype=np.float32)
        image_array = np.multiply(image_array, 1.0/255.0)  # Faster than division
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process image"
        )

def check_gemini_availability() -> bool:
    """Check if Gemini is available without consuming quota"""
    try:
        current_api_key = os.getenv("GEMINI_API_KEY")
        if not current_api_key:
            return False
        
        # Just check if we can configure the API (doesn't consume quota)
        genai.configure(api_key=current_api_key)
        return True
    except Exception:
        return False

async def get_gemini_prediction(image_bytes: bytes) -> Optional[dict]:
    """Fallback to Gemini for universal detection with quota-aware error handling"""
    global gemini_model
    
    # Hot-reload API key if changed (simplified approach)
    current_api_key = os.getenv("GEMINI_API_KEY")
    if current_api_key and not gemini_model:
        logger.info("Gemini model not initialized. Initializing now...")
        try:
            genai.configure(api_key=current_api_key)
            gemini_model = genai.GenerativeModel('gemini-flash-latest')
            logger.info("[OK] Gemini model initialized with API key")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            return None
    
    if not gemini_model:
        return None
    
    try:
        logger.info("Triggering Layer 2: Gemini Universal Detection...")
        img = Image.open(io.BytesIO(image_bytes))
        
        # Optimized prompt for faster processing
        prompt = """
        Analyze this plant image quickly. Identify the disease/condition and provide treatment.
        Return JSON: {"disease": "specific disease name", "solution": "brief treatment (2 sentences max)"}
        """
        
        response = gemini_model.generate_content([prompt, img])
        # Extract JSON from response
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        result = json.loads(text)
        return {
            "disease": result.get("disease", "Unknown Condition"),
            "solution": result.get("solution", "Consult an expert."),
            "confidence": 0.95 # Gemini is treated as high confidence
        }
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "429" in error_msg:
            logger.warning(f"⚠️ Gemini quota exceeded: {e}")
            logger.info("Layer 2 temporarily disabled due to quota. Will retry when quota resets.")
            return None
        else:
            logger.error(f"Gemini fallback failed: {e}")
            return None

async def get_enriched_disease_info(disease_name: str) -> Optional[DiseaseDetail]:
    """Fetch structured, enriched disease information from Gemini"""
    if not gemini_model:
        return None
    
    try:
        logger.info(f"Enriching data for: {disease_name}...")
        
        prompt = f"""
        Provide a detailed, professional medical-style report for the plant disease: '{disease_name}'.
        Return ONLY a JSON object with the following structure:
        {{
            "name": "Proper Disease Name",
            "causes": {{
                "details": "Detailed explanation of pathogens and environmental triggers."
            }},
            "prevention": {{
                "measures": ["Measure 1", "Measure 2", "Measure 3"]
            }},
            "treatment": {{
                "stages": [
                    {{
                        "name": "Stage 1: Early Detection",
                        "description": "Description of this stage",
                        "components": ["Action 1", "Action 2"],
                        "medications": ["Meds if any"]
                    }},
                    {{
                        "name": "Stage 2: Active Treatment",
                        "description": "Description of this stage",
                        "components": ["Action 1", "Action 2"],
                        "medications": ["Meds if any"]
                    }},
                    {{
                        "name": "Stage 3: Recovery",
                        "description": "Description of this stage",
                        "components": ["Action 1", "Action 2"],
                        "medications": []
                    }}
                ]
            }},
            "medications": [
                {{
                    "name": "Medication Name",
                    "dosage": "Specific dosage",
                    "frequency": "How often",
                    "side_effects": "Precautions or side effects"
                }}
            ],
            "emergency": {{
                "action": "Critical action if severe",
                "signs": ["Sign 1", "Sign 2"]
            }},
            "recovery": {{
                "timeline": ["Week 1: ...", "Week 2: ..."],
                "success_rate": "Estimated success rate"
            }}
        }}
        """
        
        response = gemini_model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        return DiseaseDetail(**data)
    except Exception as e:
        logger.error(f"Enrichment failed for {disease_name}: {e}")
        return None

@app.get("/enrich/{disease_name}", response_model=DiseaseDetail)
async def enrich_disease(disease_name: str):
    """Endpoint to fetch enriched disease information"""
    details = await get_enriched_disease_info(disease_name)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not enrich disease information"
        )
    return details

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with detailed status"""
    gemini_available = check_gemini_availability()
    return HealthResponse(
        status="healthy" if interpreter is not None else "unhealthy",
        model_loaded=interpreter is not None,
        labels_count=len(labels),
        solutions_count=len(solutions),
        uptime_seconds=time.time() - start_time
    )

@app.post("/predict", response_model=PredictionResponse)
async def predict_disease(file: UploadFile = File(...)):
    """Predict plant disease from uploaded image with caching and Layer 2 fallback"""
    logger.info(f"Incoming prediction request for file: {file.filename}")
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
        
        # Generate image hash for caching
        image_hash = get_image_hash(contents)
        
        # Check cache first
        cached_result = get_cached_prediction(image_hash)
        if cached_result:
            processing_time = (time.time() - start_time_request) * 1000
            logger.info(f"🚀 Returning cached result in {processing_time:.1f}ms")
            
            # Update timestamp and processing time for cached result
            cached_result["timestamp"] = datetime.now().isoformat()
            cached_result["processing_time_ms"] = processing_time
            cached_result["cached"] = True
            
            return PredictionResponse(**cached_result)
        
        # Open and preprocess image for TFLite
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            logger.error(f"Failed to open image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        processed_image = preprocess_image(image)
        
        # Run TFLite Inference (Layer 1)
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        interpreter.set_tensor(input_details[0]['index'], processed_image)
        interpreter.invoke()
        predictions = interpreter.get_tensor(output_details[0]['index'])[0]
        
        top_prediction_idx = np.argmax(predictions)
        confidence = float(predictions[top_prediction_idx])
        
        logger.info(f"Layer 1 Result: {labels[top_prediction_idx] if top_prediction_idx < len(labels) else 'unknown'} | Confidence: {confidence:.4f}")
        
        # Layer 2 Fallback Logic: If confidence is low or unknown
        if confidence < 0.7:
            # Check if Gemini is available before attempting
            if check_gemini_availability():
                logger.info(f"Confidence < 0.7 ({confidence:.3f}). Triggering Gemini Fallback...")
                gemini_res = await get_gemini_prediction(contents)
                if gemini_res:
                    processing_time = (time.time() - start_time_request) * 1000
                    logger.info(f"Layer 2 Result: {gemini_res['disease']} | Time: {processing_time:.1f}ms")
                    
                    result = {
                        "disease": f"[Universal] {gemini_res['disease']}",
                        "confidence": gemini_res['confidence'],
                        "solution": gemini_res['solution'],
                        "layer": "Advanced Analysis",
                        "details": None,
                        "timestamp": datetime.now().isoformat(),
                        "processing_time_ms": processing_time,
                        "cached": False
                    }
                    
                    # Cache the result
                    cache_prediction(image_hash, result)
                    
                    # Send Slack alert
                    send_slack_alert(
                        disease=gemini_res['disease'],
                        confidence=gemini_res['confidence'],
                        layer="Advanced Analysis",
                        image_hash=image_hash
                    )
                    
                    return PredictionResponse(**result)
                else:
                    logger.info("Layer 2 failed or quota exceeded. Using Layer 1 result.")
            else:
                logger.warning(f"Confidence < 0.7 ({confidence:.3f}) but Gemini is not available!")
        else:
            logger.info(f"Confidence >= 0.7 ({confidence:.3f}). Staying with Layer 1.")

        # Standard TFLite Result
        if top_prediction_idx < len(labels):
            disease_name = labels[top_prediction_idx]
        else:
            disease_name = "unknown"
        
        solution_key = disease_name.replace("___", " ").replace("_", " ").lower().strip()
        solution = solutions.get(solution_key, "No specific solution available. Please consult with a plant pathologist for proper diagnosis and treatment.")
        
        processing_time = (time.time() - start_time_request) * 1000
        logger.info(f"Prediction: {disease_name} (confidence: {confidence:.3f}, time: {processing_time:.1f}ms)")
        
        result = {
            "disease": disease_name,
            "confidence": confidence,
            "solution": solution,
            "layer": "Standard Analysis",
            "details": None,
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time,
            "cached": False
        }
        
        # Cache the result
        cache_prediction(image_hash, result)
        
        # Send Slack alert for high-confidence or concerning results
        if confidence > 0.8 or "disease" in disease_name.lower():
            send_slack_alert(
                disease=disease_name,
                confidence=confidence,
                layer="Standard Analysis",
                image_hash=image_hash
            )
        
        return PredictionResponse(**result)
        
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

class ReminderRequest(BaseModel):
    medication: str = Field(..., description="Medication name")
    dosage: str = Field(..., description="Dosage information")
    frequency: str = Field(..., description="Frequency of medication")
    disease: str = Field(..., description="Disease being treated")
    user_id: str = Field(default="default", description="User identifier")

class ReminderResponse(BaseModel):
    success: bool
    message: str
    reminder_id: Optional[str] = None

@app.post("/reminder", response_model=ReminderResponse)
async def create_reminder(reminder: ReminderRequest):
    """Create a medication reminder and send Slack notification"""
    try:
        # Generate unique reminder ID
        reminder_id = f"rem_{int(time.time())}_{reminder.user_id}"
        
        # Store reminder in Redis if available
        if redis_client:
            reminder_data = {
                "medication": reminder.medication,
                "dosage": reminder.dosage,
                "frequency": reminder.frequency,
                "disease": reminder.disease,
                "user_id": reminder.user_id,
                "created_at": datetime.now().isoformat(),
                "active": True
            }
            
            # Store with 30-day TTL
            redis_client.setex(
                f"reminder:{reminder_id}",
                30 * 24 * 3600,  # 30 days
                json_lib.dumps(reminder_data)
            )
            
            logger.info(f"💾 Reminder stored in Redis: {reminder_id}")
        
        # Send immediate Slack notification
        send_slack_reminder(
            medication=reminder.medication,
            dosage=reminder.dosage,
            frequency=reminder.frequency,
            disease=reminder.disease
        )
        
        return ReminderResponse(
            success=True,
            message="Reminder created and Slack notification sent",
            reminder_id=reminder_id
        )
        
    except Exception as e:
        logger.error(f"Failed to create reminder: {e}")
        return ReminderResponse(
            success=False,
            message=f"Failed to create reminder: {str(e)}"
        )

@app.get("/reminders/{user_id}")
async def get_user_reminders(user_id: str = "default"):
    """Get all active reminders for a user"""
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis not available"
        )
    
    try:
        # Get all reminder keys for user
        pattern = f"reminder:rem_*_{user_id}"
        keys = redis_client.keys(pattern)
        
        reminders = []
        for key in keys:
            reminder_data = redis_client.get(key)
            if reminder_data:
                reminder = json_lib.loads(reminder_data)
                reminder['id'] = key.split(':')[1]  # Extract reminder ID
                reminders.append(reminder)
        
        return {"reminders": reminders, "count": len(reminders)}
        
    except Exception as e:
        logger.error(f"Failed to get reminders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reminders"
        )

@app.delete("/reminder/{reminder_id}")
async def delete_reminder(reminder_id: str):
    """Delete a specific reminder"""
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis not available"
        )
    
    try:
        deleted = redis_client.delete(f"reminder:{reminder_id}")
        if deleted:
            return {"success": True, "message": "Reminder deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reminder not found"
            )
    except Exception as e:
        logger.error(f"Failed to delete reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete reminder"
        )

@app.get("/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    if not redis_client:
        return {"redis_available": False}
    
    try:
        info = redis_client.info()
        prediction_keys = len(redis_client.keys("prediction:*"))
        reminder_keys = len(redis_client.keys("reminder:*"))
        
        return {
            "redis_available": True,
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "prediction_cache_count": prediction_keys,
            "reminder_count": reminder_keys,
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        return {"redis_available": False, "error": str(e)}

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
