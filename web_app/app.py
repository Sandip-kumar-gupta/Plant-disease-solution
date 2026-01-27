import streamlit as st
import requests
import json
import io
from PIL import Image
import time
from typing import Optional, Dict, Any
from fpdf import FPDF
import base64
from datetime import datetime, timedelta
import os

# Set page config
st.set_page_config(
    page_title="Plantify",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREDICT_URL = f"{API_BASE_URL}/predict"
API_HEALTH_URL = f"{API_BASE_URL}/health"
REQUEST_TIMEOUT = 30  # seconds

# Initialize Session State for History
if 'history' not in st.session_state:
    st.session_state.history = []

# Load Custom CSS
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
        # st.error(f"Failed to load disease database: {e}")
        return {}

disease_db = load_disease_database()

def create_pdf(disease, confidence, solution, image, disease_info):
    pdf = FPDF()
    pdf.add_page()
    
    # Colors
    pdf.set_text_color(0, 0, 0)
    
    # Header
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 20, "Plantify - Medical Report", 0, 1, 'C')
    
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'R')
    pdf.line(10, 35, 200, 35)
    pdf.ln(10)
    
    # 1. Diagnosis Section
    pdf.set_font("Arial", 'B', 16)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "  1. Diagnostic Results", 0, 1, 'L', 1)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 8, "Condition Identified:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, disease_info.get('name', disease), 0, 1)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 8, "Confidence Score:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 8, f"{confidence:.1%}", 0, 1)
    pdf.ln(5)

    # 2. Root Causes
    if 'causes' in disease_info:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "  2. Root Causes", 0, 1, 'L', 1)
        pdf.ln(2)
        pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, disease_info['causes'].get('details', ''))
        pdf.ln(5)

    # 3. Prevention
    if 'prevention' in disease_info:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "  3. Prevention Strategies", 0, 1, 'L', 1)
        pdf.ln(2)
        pdf.set_font("Arial", '', 11)
        for measure in disease_info['prevention'].get('measures', []):
            pdf.cell(5)
            pdf.cell(0, 6, f"- {measure}", 0, 1)
        pdf.ln(5)

    # 4. Treatment Plan
    if 'treatment' in disease_info:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "  4. Treatment Plan", 0, 1, 'L', 1)
        pdf.ln(2)
        
        for stage in disease_info['treatment'].get('stages', []):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, stage['name'], 0, 1)
            
            pdf.set_font("Arial", 'I', 11)
            pdf.multi_cell(0, 6, stage['description'])
            
            pdf.set_font("Arial", '', 11)
            for comp in stage.get('components', []):
                pdf.cell(5)
                pdf.cell(0, 6, f"* {comp}", 0, 1)
            pdf.ln(3)

    # 5. Medications
    if 'medications' in disease_info:
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "  5. Recommended Medications", 0, 1, 'L', 1)
        pdf.ln(2)
        
        for med in disease_info.get('medications', []):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 8, med['name'], 0, 1)
            pdf.set_font("Arial", '', 11)
            pdf.cell(10)
            pdf.cell(0, 6, f"Dosage: {med.get('dosage', 'N/A')}", 0, 1)
            pdf.cell(10)
            pdf.cell(0, 6, f"Frequency: {med.get('frequency', 'N/A')}", 0, 1)
            pdf.ln(2)
            
    # 6. Emergency Signs
    if 'emergency' in disease_info:
        pdf.set_font("Arial", 'B', 16)
        pdf.set_text_color(200, 0, 0) # Red for emergency
        pdf.cell(0, 10, "  6. Emergency Signs", 0, 1, 'L', 1)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 6, f"Action Required: {disease_info['emergency'].get('action', '')}")
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 11)
        for sign in disease_info['emergency'].get('signs', []):
            pdf.cell(5)
            pdf.cell(0, 6, f"(!) {sign}", 0, 1)
        pdf.ln(5)

    # Disclaimer
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, "Disclaimer: This report is generated by an AI model. Consult an agricultural expert for professional advice.")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

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
        
        # Prepare files for upload - we need to recreate this for each attempt
        # because the file pointer might be consumed
        
        with st.spinner("🔍 Analyzing image..."):
            for attempt in range(retries):
                try:
                    # Reset file pointer for each attempt
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
                        # Server error, might be temporary
                        if attempt < retries - 1:
                            time.sleep(1 * (attempt + 1)) # Exponential backoff
                            continue
                        else:
                            st.error(f"❌ Server Error ({response.status_code}): {response.text}")
                            return None
                    else:
                        # Client error (4xx), don't retry
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
    # Check image size (50MP limit)
    if image.size[0] * image.size[1] > 50 * 1024 * 1024:
        st.error("🖼️ Image too large. Please upload an image smaller than 50 megapixels.")
        return False
    
    # Check image format
    if image.format not in ['JPEG', 'PNG', 'BMP', 'TIFF']:
        st.error("📁 Unsupported image format. Please upload JPEG, PNG, BMP, or TIFF.")
        return False
    
    return True

# --- UI Layout ---

# Hero Section
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
                    
                    # Elaborate / Search Buttons
                    st.write("") # Spacer
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
                    
                    # Solution display
                    if disease != "background":
                        # --- LAYER 2: KNOWLEDGE BASE LOOKUP ---
                        # Normalize disease name to match DB keys
                        db_key = disease.lower().replace("___", "_").replace(" ", "_")
                        
                        # Check if this is a Universal result from Gemini
                        if disease.startswith("[Universal]"):
                            disease_title = disease.replace("[Universal] ", "")
                            disease_info = {
                                "name": disease_title,
                                "causes": {"details": "Advanced AI Diagnosis: This condition was identified using our advanced foundation model because it fell outside the common crop dataset."},
                                "prevention": {"measures": ["Consult a local agricultural expert for specific prevention.", "Monitor surrounding plants for similar symptoms."]},
                                "treatment": {
                                    "stages": [
                                        {
                                            "name": "AI Recommended Treatment",
                                            "description": solution,
                                            "components": ["Follow the specific instructions provided above."],
                                            "medications": []
                                        }
                                    ]
                                },
                                "medications": [],
                                "emergency": {"action": "If the condition spreads rapidly, isolate the plant immediately.", "signs": ["Rapid leaf drop", "Stem browning"]},
                                "recovery": {"timeline": ["Timeline depends on the specific species."], "success_rate": "Variable"}
                            }
                        else:
                            disease_info = disease_db.get(db_key)
                        
                        # If not found in DB and not Universal, construct a RICH temporary object
                        if not disease_info:
                            disease_title = disease.replace("___", " - ").replace("_", " ").title()
                            disease_info = {
                                "name": disease_title,
                                "causes": {
                                    "primary": f"Fungal or bacterial infection associated with {disease_title}.",
                                    "details": f"This condition is typically caused by pathogens that thrive in specific environmental conditions. It spreads through water splashes, wind, or contaminated tools. High humidity and poor air circulation often exacerbate the spread."
                                },
                                "prevention": {
                                    "measures": [
                                        "Maintain proper plant spacing to ensure good airflow.",
                                        "Water at the base of the plant to avoid wetting foliage.",
                                        "Remove and destroy infected leaves immediately.",
                                        "Apply preventive organic fungicides early in the season.",
                                        "Rotate crops to prevent soil-borne pathogen buildup.",
                                        "Use disease-resistant plant varieties where possible.",
                                        "Sanitize gardening tools between uses."
                                    ]
                                },
                                "treatment": {
                                    "stages": [
                                        {
                                            "name": "Stage 1: Early Detection (Days 1-7)",
                                            "description": "Immediate isolation and removal of affected parts.",
                                            "components": [
                                                "Isolate the plant to prevent spread to others.",
                                                "Prune all visible infected leaves.",
                                                "Improve air circulation around the plant."
                                            ],
                                            "medications": ["Copper Fungicide Spray"]
                                        },
                                        {
                                            "name": "Stage 2: Active Treatment (Days 7-21)",
                                            "description": "Intensive treatment to halt disease progression.",
                                            "components": [
                                                "Apply fungicide every 7-10 days.",
                                                "Monitor daily for new lesions.",
                                                "Reduce watering frequency to lower humidity."
                                            ],
                                            "medications": ["Mancozeb", "Neem Oil"]
                                        },
                                        {
                                            "name": "Stage 3: Recovery (Days 21-60)",
                                            "description": "Maintenance and monitoring for recurrence.",
                                            "components": [
                                                "Resume normal care but keep foliage dry.",
                                                "Apply preventive spray monthly.",
                                                "Strengthen plant immunity with organic compost."
                                            ],
                                            "medications": []
                                        }
                                    ]
                                },
                                "medications": [
                                    {
                                        "name": "Copper Fungicide",
                                        "dosage": "2-3 tablespoons per gallon of water",
                                        "frequency": "Every 7-10 days",
                                        "side_effects": "May cause leaf burn in very hot weather."
                                    },
                                    {
                                        "name": "Neem Oil (Organic)",
                                        "dosage": "1-2 tablespoons per gallon",
                                        "frequency": "Every 7-14 days",
                                        "side_effects": "Safe for most plants, avoid direct sun after application."
                                    }
                                ],
                                "emergency": {
                                    "signs": [
                                        "More than 50% of leaves are affected.",
                                        "Disease has spread to the main stem.",
                                        "Plant is wilting rapidly despite watering.",
                                        "No improvement after 2 weeks of treatment."
                                    ],
                                    "action": "Consult an agricultural expert immediately. It may be necessary to remove and destroy the entire plant to save the rest of your garden."
                                },
                                "recovery": {
                                    "timeline": [
                                        "Week 1: Stop disease spread",
                                        "Week 2-3: New healthy growth appears",
                                        "Week 4-8: Full recovery expected"
                                    ],
                                    "success_rate": "85-90% with early treatment"
                                }
                            }

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
                                    with st.expander(f"🔔 Set Reminder ({med['name']})"):
                                        st.caption(f"Schedule a reminder for **{med['name']}**")
                                        rem_time = st.time_input("Select Time", value=datetime.now().time(), key=f"time_{i}")
                                        
                                        # Calculate datetime for the next occurrence of this time
                                        now = datetime.now()
                                        rem_dt = datetime.combine(now.date(), rem_time)
                                        if rem_dt < now:
                                            rem_dt += timedelta(days=1)
                                            
                                        # Google Calendar Link
                                        start_str = rem_dt.strftime("%Y%m%dT%H%M%S")
                                        end_str = (rem_dt + timedelta(minutes=15)).strftime("%Y%m%dT%H%M%S")
                                        
                                        event_title = f"Take {med['name']} - Plantify"
                                        event_details = f"Dosage: {med.get('dosage', 'N/A')}. Frequency: {med.get('frequency', 'N/A')}."
                                        
                                        # URL Encode
                                        import urllib.parse
                                        title_enc = urllib.parse.quote(event_title)
                                        details_enc = urllib.parse.quote(event_details)
                                        
                                        cal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title_enc}&dates={start_str}/{end_str}&details={details_enc}"
                                        
                                        st.markdown(f'<a href="{cal_url}" target="_blank" style="text-decoration:none; background-color:#4285F4; color:white; padding:8px 12px; border-radius:4px; display:inline-block;">📅 Add to Google Calendar</a>', unsafe_allow_html=True)

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
