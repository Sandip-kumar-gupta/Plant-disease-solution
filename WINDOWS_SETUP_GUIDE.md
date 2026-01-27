# 🪟 FloraGuard AI - Windows Setup Guide

## 🎯 Quick Start for Windows

### 📋 Prerequisites
Before starting, make sure you have:
- **Windows 10/11** (64-bit)
- **Internet connection**
- **Administrator privileges** (for installing software)

### 🚀 **Method 1: Automated Setup (Recommended)**

#### Step 1: Open Command Prompt or PowerShell
- Press `Win + R`, type `cmd`, press Enter
- Or press `Win + X`, select "Windows PowerShell"

#### Step 2: Navigate to Project
```cmd
cd Plant-disease-solution
```

#### Step 3: Run Windows Setup Script
```cmd
setup.bat setup
```

This will automatically:
- ✅ Check Python installation
- ✅ Check Redis availability
- ✅ Create virtual environments
- ✅ Install all dependencies
- ✅ Set up environment file

#### Step 4: Configure API Keys
```cmd
# Edit the .env file (use any text editor)
notepad .env
```

**Required**: Add your Gemini API key:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

#### Step 5: Start the System
```cmd
setup.bat start
```

#### Step 6: Access Application
- **🌐 Web Interface**: http://localhost:8502
- **📚 API Documentation**: http://localhost:8001/docs

---

## 🛠️ **Method 2: Manual Setup**

### Step 1: Install Python 3.9+
1. Go to https://www.python.org/downloads/
2. Download Python 3.9 or newer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Install Redis (Optional - for caching)
**Option A: Redis for Windows**
1. Download from: https://github.com/microsoftarchive/redis/releases
2. Extract and run `redis-server.exe`

**Option B: Docker (if you have Docker Desktop)**
```cmd
docker run -d -p 6379:6379 redis:alpine
```

**Option C: Skip Redis**
- System will work without Redis (slower performance)

### Step 3: Setup Backend
```cmd
cd backend
python -m venv backend_venv
backend_venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..
```

### Step 4: Setup Frontend
```cmd
cd web_app
python -m venv web_venv
web_venv\Scripts\activate.bat
pip install -r requirements.txt
cd ..
```

### Step 5: Configure Environment
```cmd
copy .env.example .env
notepad .env
```
Add your Gemini API key to the `.env` file.

### Step 6: Start Services

**Terminal 1 (Backend):**
```cmd
cd backend
backend_venv\Scripts\activate.bat
python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)"
```

**Terminal 2 (Frontend):**
```cmd
cd web_app
web_venv\Scripts\activate.bat
streamlit run app.py --server.port 8502
```

---

## 🔑 **Getting API Keys**

### **Gemini API Key (Required)**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)
5. Paste in `.env` file

### **Slack Bot Token (Optional)**
1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app → "From scratch"
3. Add bot scopes: `chat:write`, `chat:write.public`
4. Install to workspace
5. Copy Bot User OAuth Token (starts with `xoxb-`)

---

## 🎮 **Windows Commands Reference**

### **Using the Batch Script**
```cmd
# Complete setup
setup.bat setup

# Start all services
setup.bat start

# Stop all services
setup.bat stop

# Check status
setup.bat status

# Restart services
setup.bat restart
```

### **Manual Commands**
```cmd
# Check if Python is installed
python --version

# Check if pip is working
pip --version

# Test Redis connection (if installed)
redis-cli ping

# Check what's running on ports
netstat -an | findstr :8001
netstat -an | findstr :8502
```

---

## 🔧 **Windows-Specific Troubleshooting**

### **Python Not Found**
```cmd
# Add Python to PATH manually
# Go to: Control Panel → System → Advanced → Environment Variables
# Add Python installation path to PATH variable
# Example: C:\Users\YourName\AppData\Local\Programs\Python\Python39\
```

### **Permission Denied Errors**
```cmd
# Run Command Prompt as Administrator
# Right-click on Command Prompt → "Run as administrator"
```

### **Port Already in Use**
```cmd
# Find what's using the port
netstat -ano | findstr :8001
netstat -ano | findstr :8502

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### **Virtual Environment Issues**
```cmd
# If activation fails, try:
backend_venv\Scripts\activate.bat

# Or use full path:
C:\path\to\project\backend\backend_venv\Scripts\activate.bat
```

### **Firewall Issues**
1. Windows Defender may block the ports
2. Go to: Windows Security → Firewall & network protection
3. Allow Python through firewall
4. Or temporarily disable firewall for testing

### **Redis Connection Issues**
```cmd
# If Redis not working, system will show warnings but continue
# Check Redis status:
tasklist | findstr redis

# Start Redis manually:
redis-server.exe
```

---

## 🐳 **Docker Alternative (Windows)**

If you have Docker Desktop installed:

```cmd
# Build and run with Docker
docker-compose up --build -d

# Access same URLs:
# Web: http://localhost:8502
# API: http://localhost:8001/docs

# Stop Docker containers
docker-compose down
```

---

## 📊 **Verify Installation**

### **Check Services are Running**
1. Open browser and go to:
   - http://localhost:8502 (Web Interface)
   - http://localhost:8001/docs (API Documentation)

2. Test the system:
   - Upload a plant image
   - See AI analysis results
   - Check system status in sidebar

### **Performance Check**
```cmd
# Test API health
curl http://localhost:8001/health

# Or use PowerShell
Invoke-WebRequest -Uri http://localhost:8001/health
```

---

## 🎯 **Windows-Specific Features**

### **Desktop Shortcuts**
Create shortcuts for easy access:

**Start FloraGuard.bat:**
```cmd
@echo off
cd /d "C:\path\to\Plant-disease-solution"
setup.bat start
pause
```

**Stop FloraGuard.bat:**
```cmd
@echo off
cd /d "C:\path\to\Plant-disease-solution"
setup.bat stop
pause
```

### **Task Scheduler (Auto-start)**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., at startup)
4. Set action to run `setup.bat start`

---

## 🆘 **Common Windows Issues & Solutions**

### **Issue: "python is not recognized"**
**Solution**: Add Python to PATH or reinstall Python with "Add to PATH" checked

### **Issue: "pip is not recognized"**
**Solution**: 
```cmd
python -m pip --version
# Use 'python -m pip' instead of just 'pip'
```

### **Issue: Virtual environment activation fails**
**Solution**: Use full path to activate script:
```cmd
C:\full\path\to\backend_venv\Scripts\activate.bat
```

### **Issue: Services won't start**
**Solution**: 
1. Check if ports are free
2. Run as Administrator
3. Check Windows Firewall
4. Verify Python and dependencies installed

### **Issue: Slow performance**
**Solution**: Install Redis for caching or use Docker

---

## 🎉 **Success! What You'll See**

When everything is working:

1. **Command Prompt** shows:
   ```
   🎉 FloraGuard AI is now running!
   📱 Web Interface: http://localhost:8502
   🔧 API Documentation: http://localhost:8001/docs
   ```

2. **Web Browser** opens automatically to the FloraGuard interface

3. **System Features**:
   - Upload plant images for disease detection
   - View real-time system monitoring
   - Generate PDF reports
   - Set medication reminders
   - Access comprehensive API documentation

---

## 📞 **Windows Support**

If you need help:
1. Check the logs: `backend.log` and `frontend.log`
2. Run `setup.bat status` to check service status
3. Try `setup.bat restart` to restart services
4. Check Windows Event Viewer for system errors

**🌿 Your FloraGuard AI system is now ready on Windows! 🚀**