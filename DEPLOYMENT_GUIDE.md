# 🚀 Deployment Guide for Plantify (Updated)

This guide will help you deploy your Plant Disease Detection application.
Because this project has a **Python Backend (FastAPI)** and a **Streamlit Frontend**, we will deploy them separately.

- **Backend:** Deployed to **Vercel** (Serverless Python)
- **Frontend:** Deployed to **Streamlit Community Cloud** (Native Streamlit hosting)

---

## 1️⃣ Part 1: Deploy Backend to Vercel

The backend handles the AI model and image processing.

1.  **Login to Vercel** and click **"Add New..."** -> **"Project"**.
2.  **Import your GitHub Repository** (`Plant-disease-solution`).
3.  **Configure Project** (CRITICAL STEP):
    *   **Project Name**: You can leave it as is or change it (e.g., `plant-detection-backend`).
    *   **Framework Preset**: Select **"Other"**.
    *   **Root Directory**: Click "Edit" and select `backend`. **(This is why it failed before!)**
4.  **Environment Variables**:
    *   Expand the "Environment Variables" section.
    *   Key: `GEMINI_API_KEY`
    *   Value: `your_actual_gemini_api_key_here` (Copy this from your `.env` file).
    *   Click **Add**.
5.  Click **Deploy**.

**Note:** I have already optimized the code to use `tflite-runtime` instead of the heavy `tensorflow` library, so it should deploy within Vercel's size limits.

**Once Deployed:**
*   Vercel will give you a domain (e.g., `https://plant-detection-backend.vercel.app`).
*   **Copy this URL**. You will need it for the frontend.
*   Test it by visiting `https://YOUR-URL.vercel.app/health`. It should return `{"status": "healthy"}`.

---

## 2️⃣ Part 2: Deploy Frontend to Streamlit Cloud

The frontend is the user interface.

1.  **Login to Streamlit Cloud** (share.streamlit.io).
2.  Click **"New app"**.
3.  **Select your Repository** (`Plant-disease-solution`).
4.  **Configuration**:
    *   **Main file path**: `web_app/app.py`
5.  **Advanced Settings** (Click the arrow):
    *   **Python Version**: 3.11
    *   **Secrets**:
        *   Paste the following TOML config:
        ```toml
        API_BASE_URL = "https://YOUR-BACKEND-URL.vercel.app"
        ```
        *(Replace the URL with the one you copied from Vercel. **Do not** add a trailing slash `/`)*.
6.  Click **Deploy!**.

---

## 📱 Mobile Responsiveness

The app is now mobile-responsive. The layout will automatically adjust for phone screens.
