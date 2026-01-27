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
# Set page config
st.set_page_config(
    page_title="Plantify",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ... (Configuration and other functions remain unchanged)

    # Header
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(0, 20, "Plantify - Medical Report", 0, 1, 'C')

# ... (PDF generation logic remains unchanged)

# Hero Section
st.markdown("""
    <div class="hero-container">
        <div class="hero-title">Plantify</div>
        <div class="hero-subtitle">Advanced Plant Disease Detection & Analysis</div>
    </div>
""", unsafe_allow_html=True)

# ... (Sidebar and Dashboard remain unchanged)

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

# ... (Search buttons remain unchanged)

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

# ... (Rest of the logic remains unchanged)

                        st.download_button(
                            label="📥 Download Full Medical Report (PDF)",
                            data=pdf_bytes,
                            file_name=f"Plantify_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

# ... (Footer)

# Footer
st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem; margin-top: 2rem;">
        🌿 Plantify - Powered by Advanced AI
    </div>
""", unsafe_allow_html=True)
