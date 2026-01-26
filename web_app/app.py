import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
import os
import warnings
import json

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Set page config
st.set_page_config(
    page_title="FloraGuard AI",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Load Custom CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("web_app/styles.css")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
ASSETS_DIR = os.path.join(PROJECT_ROOT, "Plant-Disease-Detection-and-Solution", "FarmerFriendApp", "app", "src", "main", "assets")

MODEL_PATH = os.path.join(ASSETS_DIR, "model.tflite")
LABELS_PATH = os.path.join(ASSETS_DIR, "labels.txt")
DATA_PATH = os.path.join(BASE_DIR, "data.json")

@st.cache_resource
def load_model():
    try:
        # Attempt to use the TFLite interpreter
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        return interpreter
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

@st.cache_data
def load_labels():
    try:
        with open(LABELS_PATH, "r") as f:
            labels = [line.strip() for line in f.readlines()]
        return labels
    except Exception as e:
        st.error(f"Error loading labels: {e}")
        return []

@st.cache_data
def load_solutions():
    try:
        with open(DATA_PATH, "r") as f:
            solutions = json.load(f)
        return solutions
    except Exception as e:
        st.error(f"Error loading solutions: {e}")
        return {}

def predict(interpreter, image, labels, use_bgr=False):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Resize image to expected input shape (200x200 based on notebook analysis)
    input_shape = input_details[0]['shape']
    target_size = (input_shape[1], input_shape[2])
    image = image.resize(target_size)

    # Convert to numpy array
    input_data = np.array(image, dtype=np.float32)

    # Convert RGB to BGR if requested (OpenCV style)
    if use_bgr:
        input_data = input_data[..., ::-1]

    # Normalize
    input_data = input_data / 255.0  # Normalize to [0, 1]
    input_data = np.expand_dims(input_data, axis=0)

    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # Run inference
    interpreter.invoke()

    # Get output tensor
    output_data = interpreter.get_tensor(output_details[0]['index'])
    
    # Get top prediction
    prediction_index = np.argmax(output_data)
    confidence = output_data[0][prediction_index]
    
    predicted_label = labels[prediction_index] if prediction_index < len(labels) else "Unknown"
    
    return predicted_label, confidence

# --- UI Layout ---

# Hero Section
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">FloraGuard AI</div>
        <div class="hero-subtitle">Advanced Plant Disease Detection & Analysis</div>
    </div>
""", unsafe_allow_html=True)

# Main Content
col1, col2 = st.columns([1, 2])

# Load resources
interpreter = load_model()
labels = load_labels()
solutions = load_solutions()

if interpreter and labels:
    uploaded_file = st.file_uploader("Upload a plant leaf image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            image = Image.open(uploaded_file).convert("RGB")
            
            # Display Image
            st.image(image, caption="Analyzed Image", use_column_width=True)
            
            # Advanced Options
            use_bgr = st.checkbox("Use Legacy Mode (BGR Format)", value=False, help="Try this if detection is inaccurate. Some older models were trained with OpenCV (BGR) instead of RGB.")

            # Prediction
            with st.spinner("Running AI Analysis..."):
                predicted_label, confidence = predict(interpreter, image, labels, use_bgr=use_bgr)
            
            # Get Solution
            solution = solutions.get(predicted_label, "No solution information available for this condition.")

            # Result Display
            st.markdown(f"""
                <div class="prediction-card">
                    <div style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 0.5rem;">DETECTED CONDITION</div>
                    <div class="prediction-label">{predicted_label.title()}</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: {confidence * 100}%;"></div>
                    </div>
                    <div style="margin-top: 0.5rem; color: #9ca3af; font-size: 0.8rem;">Confidence: {confidence:.1%}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Solution Display
            st.markdown(f"""
                <div style="background: rgba(74, 222, 128, 0.1); border: 1px solid rgba(74, 222, 128, 0.2); border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
                    <h3 style="color: #4ade80; margin-top: 0;">Recommended Solution</h3>
                    <p style="font-size: 1.1rem;">{solution}</p>
                </div>
            """, unsafe_allow_html=True)

            if predicted_label == "background":
                 st.info("💡 **Tip:** For best results, please upload a clear image of a single plant leaf against a plain background.")
            
        except Exception as e:
            st.error(f"Error processing image: {e}")
else:
    st.warning("System initialization failed. Please check model paths.")
