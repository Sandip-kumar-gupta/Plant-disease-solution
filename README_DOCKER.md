# 🐳 FloraGuard AI - Docker Deployment Guide

This project is fully containerized using Docker, allowing you to run the entire stack (Backend API + Frontend Web App) with a single command.

## Prerequisites

- [Docker](https://www.docker.com/get-started) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop).

## 🚀 Quick Start

1.  **Build and Run**
    Open a terminal in the project root and run:
    ```bash
    docker-compose up --build
    ```

2.  **Access the App**
    - **Web App**: Open [http://localhost:8501](http://localhost:8501) in your browser.
    - **Backend API Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs) to see the API Swagger UI.

3.  **Stop the App**
    Press `Ctrl+C` in the terminal, or run:
    ```bash
    docker-compose down
    ```

## 🏗️ Architecture

- **Backend (`floraguard-backend`)**:
    - Built with **FastAPI** and **TensorFlow Lite**.
    - Runs on port `8000`.
    - Handles image processing and disease prediction.
    - Health check: `http://localhost:8000/health`

- **Frontend (`floraguard-frontend`)**:
    - Built with **Streamlit**.
    - Runs on port `8501`.
    - Connects to the backend via the internal Docker network (`http://backend:8000`).

## 🛠️ Troubleshooting

- **"Port already in use"**: Ensure no other services are running on ports 8000 or 8501.
- **"Backend Offline" in Web App**: Wait a few seconds. The frontend might start faster than the backend. The app has built-in retry logic and will connect automatically once the backend is ready.
