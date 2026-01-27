import streamlit as st
import requests
import json
import io
from PIL import Image
import time
from typing import Optional, Dict, Any
from fpdf import FPDF
import base64
from datetime import datetime
import os

# Set page config
st.set_page_config(
    page_title="Plantify",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")
API_PREDICT_URL = f"{API_BASE_URL}/predict"
API_ENRICH_URL = f"{API_BASE_URL}/enrich"
API_HEALTH_URL = f"{API_BASE_URL}/health"
API_REMINDER_URL = f"{API_BASE_URL}/reminder"
API_REMINDERS_URL = f"{API_BASE_URL}/reminders"
API_CACHE_STATS_URL = f"{API_BASE_URL}/cache/stats"
REQUEST_TIMEOUT = 30  # seconds

# Initialize Session State for History and Reminders
if 'history' not in st.session_state:
    st.session_state.history = []

if 'user_id' not in st.session_state:
    st.session_state.user_id = "default"  # In production, this would be actual user ID

# Load Custom CSS
def create_reminder_via_api(medication: str, dosage: str, frequency: str, disease: str) -> bool:
    """Create reminder via backend API with Redis storage and Slack notification"""
    try:
        payload = {
            "medication": medication,
            "dosage": dosage,
            "frequency": frequency,
            "disease": disease,
            "user_id": st.session_state.user_id
        }
        
        response = requests.post(API_REMINDER_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                st.success(f"✅ {result.get('message', 'Reminder created successfully!')}")
                return True
            else:
                st.error(f"❌ {result.get('message', 'Failed to create reminder')}")
                return False
        else:
            st.error(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        st.error(f"❌ Failed to create reminder: {e}")
        # Fallback to local storage
        add_reminder(medication, dosage, frequency, disease)
        return False

def get_reminders_via_api() -> list:
    """Get reminders from backend API (Redis)"""
    try:
        response = requests.get(f"{API_REMINDERS_URL}/{st.session_state.user_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("reminders", [])
        else:
            return []
            
    except Exception as e:
        # Fallback to session state
        return st.session_state.get('reminders', [])

def delete_reminder_via_api(reminder_id: str) -> bool:
    """Delete reminder via backend API"""
    try:
        response = requests.delete(f"{API_REMINDER_URL}/{reminder_id}", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_cache_stats() -> dict:
    """Get Redis cache statistics"""
    try:
        response = requests.get(API_CACHE_STATS_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"redis_available": False}
    except:
        return {"redis_available": False}
def add_reminder(medication_name: str, dosage: str, frequency: str, disease: str) -> None:
    """Add a new reminder to the session state (fallback)"""
    from datetime import datetime, timedelta
    
    # Parse frequency to determine next reminder time
    next_reminder = datetime.now()
    if "daily" in frequency.lower() or "day" in frequency.lower():
        next_reminder += timedelta(days=1)
    elif "twice" in frequency.lower() or "2" in frequency:
        next_reminder += timedelta(hours=12)
    elif "three" in frequency.lower() or "3" in frequency:
        next_reminder += timedelta(hours=8)
    elif "hour" in frequency.lower():
        # Extract hours if mentioned
        import re
        hours = re.findall(r'\d+', frequency)
        if hours:
            next_reminder += timedelta(hours=int(hours[0]))
        else:
            next_reminder += timedelta(hours=6)  # Default
    else:
        next_reminder += timedelta(hours=24)  # Default to daily
    
    if 'reminders' not in st.session_state:
        st.session_state.reminders = []
    
    reminder = {
        'id': len(st.session_state.reminders) + 1,
        'medication': medication_name,
        'dosage': dosage,
        'frequency': frequency,
        'disease': disease,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'next_reminder': next_reminder.strftime('%Y-%m-%d %H:%M'),
        'active': True
    }
    
    st.session_state.reminders.append(reminder)

def get_active_reminders() -> list:
    """Get all active reminders from API or fallback to session state"""
    try:
        # Try to get from API first
        api_reminders = get_reminders_via_api()
        if api_reminders:
            return [r for r in api_reminders if r.get('active', True)]
    except:
        pass
    
    # Fallback to session state
    if 'reminders' not in st.session_state:
        st.session_state.reminders = []
    return [r for r in st.session_state.reminders if r.get('active', True)]

def remove_reminder(reminder_id: str) -> None:
    """Remove a reminder by ID via API or session state"""
    try:
        # Try API first
        if delete_reminder_via_api(reminder_id):
            st.success("✅ Reminder deleted successfully!")
            return
    except:
        pass
    
    # Fallback to session state
    if 'reminders' not in st.session_state:
        st.session_state.reminders = []
    st.session_state.reminders = [r for r in st.session_state.reminders if str(r['id']) != str(reminder_id)]

def check_due_reminders() -> list:
    """Check for reminders that are due now"""
    from datetime import datetime
    now = datetime.now()
    due_reminders = []
    
    active_reminders = get_active_reminders()
    for reminder in active_reminders:
        try:
            reminder_time = datetime.strptime(reminder['next_reminder'], '%Y-%m-%d %H:%M')
            if reminder_time <= now:
                due_reminders.append(reminder)
        except:
            continue
    
    return due_reminders

def load_css(file_name: str) -> None:
    """Load custom CSS file"""
    try:
        # Use absolute path for reliability
        base_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(base_dir, "styles.css")
        
        with open(css_path, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file not found at {css_path}. Using default styling.")

load_css("styles.css")

# Check for due reminders and show notifications
due_reminders = check_due_reminders()
if due_reminders:
    st.sidebar.markdown("### 🔔 **MEDICATION REMINDERS DUE!**")
    for reminder in due_reminders:
        st.sidebar.error(f"""
        **{reminder['medication']}**  
        💊 {reminder['dosage']}  
        ⏰ {reminder['frequency']}  
        🦠 For: {reminder['disease']}
        """)

# Sidebar: Active Reminders Management
st.sidebar.markdown("---")
st.sidebar.markdown("### 💊 Active Reminders")

active_reminders = get_active_reminders()
if active_reminders:
    st.sidebar.markdown(f"📋 **{len(active_reminders)} active reminder(s)**")
    
    with st.sidebar.expander("🔍 View All Reminders", expanded=False):
        for reminder in active_reminders:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                **{reminder['medication']}**  
                💊 {reminder['dosage']}  
                ⏰ {reminder['frequency']}  
                📅 Next: {reminder['next_reminder']}
                """)
            with col2:
                if st.button("🗑️", key=f"del_{reminder['id']}", help="Delete reminder"):
                    remove_reminder(str(reminder['id']))
                    st.rerun()
            st.markdown("---")
else:
    st.sidebar.info("No active reminders")

# Sidebar: Quick Actions
st.sidebar.markdown("### ⚡ Quick Actions")
if st.sidebar.button("🔄 Check for Due Reminders"):
    st.rerun()

if st.sidebar.button("🗑️ Clear All Reminders"):
    try:
        # Clear from API if available
        active_reminders = get_active_reminders()
        for reminder in active_reminders:
            delete_reminder_via_api(str(reminder.get('id', '')))
    except:
        pass
    
    # Clear session state as fallback
    st.session_state.reminders = []
    st.sidebar.success("All reminders cleared!")
    st.rerun()

# Load Disease Database
@st.cache_data
def load_disease_database():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Assuming docs is at the same level as web_app
        db_path = os.path.join(os.path.dirname(base_dir), "docs", "DISEASE_DATABASE.json")
        with open(db_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {}

disease_db = load_disease_database()

def sanitize_text_for_pdf(text: str) -> str:
    """Sanitize text for PDF generation by replacing problematic Unicode characters"""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Replace common problematic Unicode characters
    replacements = {
        '–': '-',  # em-dash to hyphen
        '—': '-',  # en-dash to hyphen
        ''': "'",  # smart quote to regular quote
        ''': "'",  # smart quote to regular quote
        '"': '"',  # smart quote to regular quote
        '"': '"',  # smart quote to regular quote
        '…': '...',  # ellipsis to three dots
        '°': ' degrees',  # degree symbol
        '×': 'x',  # multiplication sign
        '•': '-',  # bullet point to hyphen
        '*': '-',  # asterisk to hyphen for lists
        '®': '(R)',  # registered trademark
        '™': '(TM)',  # trademark
        '©': '(C)',  # copyright
        '±': '+/-',  # plus-minus
        '≤': '<=',  # less than or equal
        '≥': '>=',  # greater than or equal
        '≠': '!=',  # not equal
        '→': '->',  # right arrow
        '←': '<-',  # left arrow
        '↑': '^',   # up arrow
        '↓': 'v',   # down arrow
    }
    
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters
    try:
        text = text.encode('ascii', 'ignore').decode('ascii')
    except:
        # Fallback: remove all non-printable characters
        text = ''.join(char for char in text if ord(char) < 128 and char.isprintable() or char.isspace())
    
    return text

def create_pdf(disease, confidence, solution, image, disease_info):
    # Use fpdf2 which handles UTF-8 better
    pdf = FPDF()
    pdf.add_page()
    
    # Colors
    pdf.set_text_color(0, 0, 0)
    
    # Header
    pdf.set_font("helvetica", 'B', 24)
    pdf.cell(0, 20, "Plantify - Medical Report", 0, 1, 'C')
    
    pdf.set_font("helvetica", 'I', 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'R')
    pdf.line(10, 35, 200, 35)
    pdf.ln(10)
    
    # 1. Diagnosis Section
    pdf.set_font("helvetica", 'B', 16)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "  1. Diagnostic Results", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(40, 8, "Condition Identified:", 0, 0)
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 8, sanitize_text_for_pdf(str(disease_info.get('name', disease))), 0, 1)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(40, 8, "Confidence Score:", 0, 0)
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 8, f"{confidence:.1%}", 0, 1)
    pdf.ln(5)

    # 2. Root Causes
    if disease_info.get('causes'):
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "  2. Root Causes", 0, 1, 'L', fill=True)
        pdf.ln(2)
        pdf.set_font("helvetica", '', 11)
        pdf.multi_cell(0, 6, sanitize_text_for_pdf(str(disease_info['causes'].get('details', ''))))
        pdf.ln(5)

    # 3. Prevention
    if disease_info.get('prevention'):
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "  3. Prevention Strategies", 0, 1, 'L', fill=True)
        pdf.ln(2)
        pdf.set_font("helvetica", '', 11)
        for measure in disease_info['prevention'].get('measures', []):
            pdf.cell(5)
            pdf.cell(0, 6, sanitize_text_for_pdf(f"- {str(measure)}"), 0, 1)
        pdf.ln(5)

    # 4. Treatment Plan
    if disease_info.get('treatment'):
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "  4. Treatment Plan", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        for stage in disease_info['treatment'].get('stages', []):
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 8, sanitize_text_for_pdf(str(stage['name'])), 0, 1)
            
            pdf.set_font("helvetica", 'I', 11)
            pdf.multi_cell(0, 6, sanitize_text_for_pdf(str(stage['description'])))
            
            pdf.set_font("helvetica", '', 11)
            for comp in stage.get('components', []):
                pdf.cell(5)
                pdf.cell(0, 6, sanitize_text_for_pdf(f"* {str(comp)}"), 0, 1)
            pdf.ln(3)

    # 5. Medications
    if disease_info.get('medications'):
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "  5. Recommended Medications", 0, 1, 'L', fill=True)
        pdf.ln(2)
        
        for med in disease_info.get('medications', []):
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 8, sanitize_text_for_pdf(str(med['name'])), 0, 1)
            pdf.set_font("helvetica", '', 11)
            pdf.cell(10)
            pdf.cell(0, 6, sanitize_text_for_pdf(f"Dosage: {str(med.get('dosage', 'N/A'))}"), 0, 1)
            pdf.cell(10)
            pdf.cell(0, 6, sanitize_text_for_pdf(f"Frequency: {str(med.get('frequency', 'N/A'))}"), 0, 1)
            pdf.ln(2)
            
    # 6. Emergency Signs
    if disease_info.get('emergency'):
        pdf.set_font("helvetica", 'B', 16)
        pdf.set_text_color(200, 0, 0) # Red for emergency
        pdf.cell(0, 10, "  6. Emergency Signs", 0, 1, 'L', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font("helvetica", 'B', 11)
        pdf.multi_cell(0, 6, sanitize_text_for_pdf(f"Action Required: {str(disease_info['emergency'].get('action', ''))}"))
        pdf.ln(2)
        
        pdf.set_font("helvetica", '', 11)
        for sign in disease_info['emergency'].get('signs', []):
            pdf.cell(5)
            pdf.cell(0, 6, sanitize_text_for_pdf(f"(!) {str(sign)}"), 0, 1)
        pdf.ln(5)

    # Disclaimer
    pdf.set_y(-30)
    pdf.set_font("helvetica", 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Disclaimer: This report is generated by an AI model. Consult an agricultural expert for professional advice.")
    
    # fpdf2 returns bytearray, convert to bytes for Streamlit
    output = pdf.output()
    if isinstance(output, bytearray):
        return bytes(output)
    else:
        return output

def enrich_via_api(disease_name: str) -> Optional[Dict[str, Any]]:
    """Fetch enriched disease information from backend"""
    try:
        # Clean name for URL
        clean_name = disease_name.replace("[Universal] ", "").strip()
        url = f"{API_ENRICH_URL}/{clean_name}"
        
        response = requests.get(url, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None
    except Exception as e:
        st.error(f"Failed to enrich data: {e}")
        return None

def check_backend_health() -> Dict[str, Any]:
    """Check if backend API is healthy"""
    try:
        response = requests.get(API_HEALTH_URL, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"status": "unreachable", "error": str(e)}

def predict_via_api(image: Image.Image, retries: int = 3) -> Optional[Dict[str, Any]]:
    """Send image to backend API for prediction with retry logic"""
    try:
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        with st.spinner("🔍 Analyzing image..."):
            for attempt in range(retries):
                try:
                    img_byte_arr.seek(0)
                    files = {"file": ("image.jpg", img_byte_arr, "image/jpeg")}
                    
                    response = requests.post(
                        API_PREDICT_URL, 
                        files=files, 
                        timeout=REQUEST_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code >= 500:
                        if attempt < retries - 1:
                            time.sleep(1 * (attempt + 1))
                            continue
                        else:
                            st.error(f"❌ Server Error ({response.status_code}): {response.text}")
                            return None
                    else:
                        error_detail = response.json().get('detail', 'Unknown error') if response.headers.get('content-type') == 'application/json' else response.text
                        st.error(f"❌ API Error ({response.status_code}): {error_detail}")
                        return None
                        
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < retries - 1:
                        time.sleep(1 * (attempt + 1))
                        continue
                    else:
                        if isinstance(e, requests.exceptions.Timeout):
                            st.error("⏱️ Request timed out. The backend might be busy.")
                        else:
                            st.error("🔌 Cannot connect to backend API. Please ensure the backend server is running.")
                        return None
                        
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

def validate_image(image: Image.Image) -> bool:
    """Validate uploaded image"""
    if image.size[0] * image.size[1] > 50 * 1024 * 1024:
        st.error("🖼️ Image too large. Please upload an image smaller than 50 megapixels.")
        return False
    
    if image.format not in ['JPEG', 'PNG', 'BMP', 'TIFF']:
        st.error("📁 Unsupported image format. Please upload JPEG, PNG, BMP, or TIFF.")
        return False
    
    return True

# --- UI Layout ---

# Hero Section with Reminder Notifications
due_count = len(check_due_reminders())
if due_count > 0:
    st.markdown(f"""
        <div class="hero-container" style="background: linear-gradient(135deg, #ff6b6b, #ee5a24);">
            <div class="hero-title">Plantify</div>
            <div class="hero-subtitle">Advanced Plant Disease Detection & Analysis</div>
            <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 8px; margin-top: 10px;">
                ⚠️ <strong>{due_count} medication reminder(s) due!</strong> Check sidebar →
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="hero-container">
            <div class="hero-title">Plantify</div>
            <div class="hero-subtitle">Advanced Plant Disease Detection & Analysis</div>
        </div>
    """, unsafe_allow_html=True)

# Backend Health Check
with st.sidebar:
    st.markdown("### 🔧 System Status")
    health_status = check_backend_health()
    
    if health_status.get("status") == "healthy":
        st.success("✅ Backend Online")
        st.info(f"📊 Model loaded: {health_status.get('model_loaded', 'Unknown')}")
        st.info(f"🏷️ Labels: {health_status.get('labels_count', 'Unknown')}")
        st.info(f"💊 Solutions: {health_status.get('solutions_count', 'Unknown')}")
        uptime = health_status.get('uptime_seconds', 0)
        st.info(f"⏱️ Uptime: {uptime:.1f}s")
        
        # Redis Cache Status
        cache_stats = get_cache_stats()
        if cache_stats.get("redis_available"):
            st.success("🚀 Redis Cache Online")
            st.caption(f"📊 Cached Predictions: {cache_stats.get('prediction_cache_count', 0)}")
            st.caption(f"🔔 Stored Reminders: {cache_stats.get('reminder_count', 0)}")
            st.caption(f"💾 Memory Used: {cache_stats.get('used_memory_human', '0B')}")
        else:
            st.warning("⚠️ Redis Cache Offline")
            st.caption("Using fallback storage")
            
    else:
        st.error("❌ Backend Offline")
        st.error(f"Error: {health_status.get('error', 'Unknown')}")
        st.warning("Please start the backend server:\n```bash\ncd backend\npython -m uvicorn main:app --reload\n```")

    # Dashboard Section
    st.markdown("---")
    st.markdown("### 📊 Live Dashboard")
    
    if st.session_state.history:
        total_scans = len(st.session_state.history)
        healthy_count = sum(1 for item in st.session_state.history if "healthy" in item["disease"].lower())
        diseased_count = total_scans - healthy_count
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.metric("Total Scans", total_scans)
        with col_d2:
            st.metric("Disease Rate", f"{(diseased_count/total_scans)*100:.0f}%")
            
        # Disease Distribution Chart
        disease_counts = {}
        for item in st.session_state.history:
            d_name = item["disease"].split("___")[-1].replace("_", " ")
            disease_counts[d_name] = disease_counts.get(d_name, 0) + 1
            
        st.caption("Disease Distribution")
        st.bar_chart(disease_counts, color="#4CAF50")
    else:
        st.info("Start scanning to see live stats.")

    # History Section
    st.markdown("---")
    st.markdown("### 📜 Scan History")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])): # Show last 5
            with st.expander(f"{item['time']} - {item['disease']}"):
                st.write(f"**Confidence:** {item['confidence']:.1%}")
                st.write(f"**Solution:** {item['solution'][:50]}...")
    else:
        st.info("No scans yet.")

# Main Content
if health_status.get("status") == "healthy":
    uploaded_file = st.file_uploader(
        "📤 Upload a plant leaf image", 
        type=["jpg", "jpeg", "png", "bmp", "tiff"],
        help="For best results, upload a clear image of a single plant leaf"
    )

    if uploaded_file is not None:
        try:
            # Load and validate image
            image = Image.open(uploaded_file)
            
            if not validate_image(image):
                st.stop()
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Display image info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.image(image, caption="📸 Uploaded Image", use_column_width=True)
            
            with col2:
                st.markdown("### 📋 Image Info")
                st.write(f"**Size:** {image.size[0]} × {image.size[1]}")
                st.write(f"**Format:** {image.format}")
                st.write(f"**Mode:** {image.mode}")
            
            # Prediction button
            if st.button("🔍 Analyze Plant", type="primary", use_container_width=True):
                start_time = time.time()
                result = predict_via_api(image)
                
                if result:
                    disease = result.get("disease", "Unknown")
                    confidence = result.get("confidence", 0.0)
                    solution = result.get("solution", "No solution available")
                    processing_time = result.get("processing_time_ms", 0)
                    
                    # Save to History
                    st.session_state.history.append({
                        "time": datetime.now().strftime("%H:%M"),
                        "disease": disease,
                        "confidence": confidence,
                        "solution": solution
                    })
                    
                    st.markdown(f"""
                        <div class="prediction-card">
                            <div style="color: #888; font-size: 0.8rem; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 2px;">🔬 Detected Condition</div>
                            <div class="prediction-label">{disease.replace("___", " - ").replace("_", " ").replace("[Universal] ", "").title()}</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {confidence * 100}%;"></div>
                            </div>
                            <div style="margin-top: 1rem; color: #666; font-size: 0.8rem; font-family: monospace;">
                                CONFIDENCE: {confidence:.1%} | PROCESSING: {processing_time:.1f}ms
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # --- NEW: PROGRESSIVE LOADING ---
                    st.write("") # Spacer
                    
                    # Show a placeholder for the enrichment
                    enrichment_container = st.container()
                    
                    with enrichment_container:
                        with st.spinner("🧬 Fetching detailed medical analysis..."):
                            disease_info = enrich_via_api(disease)
                    
                    if not disease_info:
                        st.warning("⚠️ Could not fetch detailed medical information for this condition.")
                        st.info(f"**Basic Solution:** {solution}")
                        st.stop()

                    # Elaborate / Search Buttons
                    col_search_1, col_search_2 = st.columns(2)
                    
                    with col_search_1:
                        search_query = f"{disease} plant disease details symptoms"
                        st.link_button("🔍 Learn More About Disease", f"https://www.google.com/search?q={search_query}", use_container_width=True)
                        
                    with col_search_2:
                        cure_query = f"{disease} plant disease treatment and organic cure"
                        st.link_button("💊 Find Detailed Cures", f"https://www.google.com/search?q={cure_query}", use_container_width=True)

                    # Detailed Analysis Expander
                    with st.expander("ℹ️ View Detailed Analysis"):
                        st.markdown(f"""
                        **Diagnostic Report:**
                        - **Condition:** `{disease}`
                        - **Confidence:** `{confidence:.4f}`
                        - **Analysis Time:** `{processing_time:.1f}ms`
                        
                        The AI system has analyzed the visual patterns on the leaf (texture, color, and lesions) and matched them with known disease signatures. 
                        The confidence score indicates the model's certainty. A score above 80% is generally reliable.
                        """)
                    
                    if disease != "background":
                        # --- LAYER 3: ENHANCED DISPLAY ---
                        
                        # 1. Root Causes
                        st.markdown(f"### 🔬 Root Causes")
                        st.write(disease_info["causes"]["details"])
                        
                        # 2. Prevention Strategies
                        with st.expander("🛡️ Prevention Strategies", expanded=False):
                            for measure in disease_info["prevention"]["measures"]:
                                 st.info(f"• {measure}")

                        # 3. Treatment Plan (Tabs for Stages)
                        st.markdown("### 🩺 Treatment Plan")
                        t_tabs = st.tabs([s["name"].split(":")[0] for s in disease_info["treatment"]["stages"]])
                        
                        for i, tab in enumerate(t_tabs):
                            stage = disease_info["treatment"]["stages"][i]
                            with tab:
                                st.markdown(f"**{stage['name']}**")
                                st.write(f"*{stage['description']}*")
                                for comp in stage["components"]:
                                    st.write(f"- {comp}")
                                if stage["medications"]:
                                    st.caption(f"**Recommended Meds:** {', '.join(stage['medications'])}")

                        # 4. Medications & Dosages
                        if disease_info.get("medications"):
                            st.markdown("### 💊 Medications & Dosages")
                            cols = st.columns(len(disease_info["medications"]))
                            for i, med in enumerate(disease_info["medications"]):
                                with cols[i]:
                                    st.markdown(f"""
                                    <div style="border:1px solid #444; padding:10px; border-radius:5px; background:rgba(255,255,255,0.05);">
                                        <strong>{med['name']}</strong><br>
                                        <span style="font-size:0.8em">
                                        <b>Dosage:</b> {med['dosage']}<br>
                                        <b>Freq:</b> {med['frequency']}<br>
                                        <b>Note:</b> {med['side_effects']}
                                        </span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    if st.button(f"🔔 Set Reminder ({med['name']})", key=f"rem_{i}"):
                                        success = create_reminder_via_api(
                                            medication=med['name'],
                                            dosage=med.get('dosage', 'As prescribed'),
                                            frequency=med.get('frequency', 'As needed'),
                                            disease=disease
                                        )
                                        if success:
                                            st.balloons()
                                        st.rerun()

                        # 5. Emergency Signs
                        st.markdown("### ⚠️ Emergency Signs")
                        st.error(f"**Action Required:** {disease_info['emergency']['action']}")
                        for sign in disease_info["emergency"]["signs"]:
                            st.write(f"🚨 {sign}")

                        # 6. Expected Recovery
                        with st.expander("📊 Expected Recovery Timeline"):
                            for step in disease_info["recovery"]["timeline"]:
                                st.write(f"✅ {step}")
                            st.caption(f"**Success Rate:** {disease_info['recovery']['success_rate']}")

                        # PDF Download
                        pdf_bytes = create_pdf(disease, confidence, solution, image, disease_info)
                        st.download_button(
                            label="📥 Download Full Medical Report (PDF)",
                            data=pdf_bytes,
                            file_name=f"Plantify_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                    else:
                        st.info("💡 **Tip:** For best results, please upload a clear image of a single plant leaf against a plain background.")
                    
                    # Performance metrics
                    total_time = (time.time() - start_time) * 1000
                    st.caption(f"⚡ Total request time: {total_time:.1f}ms")
                    
        except Exception as e:
            st.error(f"❌ Error processing image: {str(e)}")
            st.info("Please try uploading a different image or check the image format.")

else:
    st.error("🚫 Cannot connect to backend API. Please ensure the backend server is running.")
    st.code("""
# Start the backend server:
cd backend
python -m uvicorn main:app --reload

# Or using Docker:
cd backend
docker build -t floraguard-backend .
docker run -p 8000:8000 floraguard-backend
    """, language="bash")

# Footer
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem;">
        🌿 Plantify - Powered by Advanced AI
    </div>
""", unsafe_allow_html=True)
