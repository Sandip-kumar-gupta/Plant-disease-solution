# 🪟 FloraGuard AI - Windows Quick Start

## ⚡ **Super Quick Setup (5 Minutes)**

### 1️⃣ **Open Command Prompt**
- Press `Win + R`
- Type `cmd` and press Enter

### 2️⃣ **Navigate to Project**
```cmd
cd Plant-disease-solution
```

### 3️⃣ **Run Setup**
```cmd
setup.bat setup
```
*This installs everything automatically!*

### 4️⃣ **Add API Key**
```cmd
notepad .env
```
Replace `your_gemini_api_key_here` with your actual Gemini API key.

**Get API Key**: Go to https://makersuite.google.com/app/apikey

### 5️⃣ **Start System**
```cmd
setup.bat start
```

### 6️⃣ **Open Browser**
The system will automatically open: http://localhost:8502

## 🎯 **That's It!**

You can now:
- 📸 Upload plant images
- 🔍 Get AI disease detection
- 📊 View system monitoring
- 📋 Generate PDF reports
- 🔔 Set medication reminders

## 🛠️ **Quick Commands**

```cmd
setup.bat start    # Start the system
setup.bat stop     # Stop the system
setup.bat status   # Check if running
setup.bat restart  # Restart everything
```

## 🆘 **If Something Goes Wrong**

### **Python Not Found?**
1. Install Python from: https://www.python.org/downloads/
2. ✅ **Check "Add Python to PATH"** during installation

### **Services Won't Start?**
```cmd
# Check what's using the ports
netstat -an | findstr :8001
netstat -an | findstr :8502

# Restart everything
setup.bat restart
```

### **Need Help?**
- Check `backend.log` and `frontend.log` files
- Read [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) for detailed instructions

## 🌟 **Features You'll Get**

- ⚡ **Lightning Fast**: 2-3ms response time with caching
- 🧠 **Dual AI**: TensorFlow Lite + Google Gemini
- 📱 **Modern Interface**: Real-time monitoring
- 🔔 **Smart Alerts**: Slack notifications (optional)
- 📋 **Professional Reports**: PDF generation
- 🔒 **Secure**: No data stored permanently

**🌿 Welcome to FloraGuard AI - Your Plant Health Assistant! 🚀**