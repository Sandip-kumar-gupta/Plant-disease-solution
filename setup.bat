@echo off
REM FloraGuard AI - Windows Setup Script
REM This script sets up the complete FloraGuard AI system on Windows

setlocal enabledelayedexpansion

echo 🌿 FloraGuard AI - Windows Setup Script
echo =====================================

REM Colors for output (limited in batch)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Function to print status
:print_status
echo %GREEN%[INFO]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:print_error
echo %RED%[ERROR]%NC% %~1
goto :eof

:print_header
echo %BLUE%%~1%NC%
goto :eof

REM Check if Python 3.9+ is installed
:check_python
call :print_header "🐍 Checking Python version..."
python --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Python not found. Please install Python 3.9+ from https://python.org"
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :print_status "Python %PYTHON_VERSION% found ✅"

REM Extract major and minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    call :print_error "Python 3.9+ required. Found: %PYTHON_VERSION%"
    pause
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 if %PYTHON_MINOR% LSS 9 (
    call :print_error "Python 3.9+ required. Found: %PYTHON_VERSION%"
    pause
    exit /b 1
)
goto :eof

REM Check if Redis is available (Windows)
:check_redis
call :print_header "🔴 Checking Redis..."
redis-server --version >nul 2>&1
if errorlevel 1 (
    call :print_warning "Redis not found. Please install Redis for Windows:"
    echo 1. Download from: https://github.com/microsoftarchive/redis/releases
    echo 2. Or use Docker: docker run -d -p 6379:6379 redis:alpine
    echo 3. Or use WSL2 with Linux Redis
    echo.
    echo For now, the system will work without caching (slower performance)
    set REDIS_AVAILABLE=false
) else (
    for /f "tokens=2" %%i in ('redis-server --version 2^>^&1') do set REDIS_VERSION=%%i
    call :print_status "Redis found ✅"
    set REDIS_AVAILABLE=true
)
goto :eof

REM Setup environment file
:setup_env
call :print_header "⚙️ Setting up environment..."
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        call :print_status "Created .env file from template"
        call :print_warning "Please edit .env file with your API keys before running the system"
    ) else (
        call :print_error ".env.example not found"
        pause
        exit /b 1
    )
) else (
    call :print_status ".env file already exists"
)
goto :eof

REM Setup backend
:setup_backend
call :print_header "🔧 Setting up Backend..."
cd backend

if not exist "backend_venv" (
    call :print_status "Creating Python virtual environment..."
    python -m venv backend_venv
)

call :print_status "Activating virtual environment..."
call backend_venv\Scripts\activate.bat

call :print_status "Installing backend dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

call :print_status "Backend setup complete ✅"
cd ..
goto :eof

REM Setup frontend
:setup_frontend
call :print_header "🎨 Setting up Frontend..."
cd web_app

if not exist "web_venv" (
    call :print_status "Creating Python virtual environment..."
    python -m venv web_venv
)

call :print_status "Activating virtual environment..."
call web_venv\Scripts\activate.bat

call :print_status "Installing frontend dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

call :print_status "Frontend setup complete ✅"
cd ..
goto :eof

REM Start Redis (if available)
:start_redis
if "%REDIS_AVAILABLE%"=="true" (
    call :print_header "🚀 Starting Redis..."
    tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        call :print_status "Redis is already running"
    ) else (
        call :print_status "Starting Redis server..."
        start /B redis-server
        timeout /t 2 >nul
        tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
        if "%ERRORLEVEL%"=="0" (
            call :print_status "Redis started successfully ✅"
        ) else (
            call :print_warning "Redis failed to start, continuing without caching"
        )
    )
) else (
    call :print_warning "Redis not available, running without caching"
)
goto :eof

REM Function to start services
:start_services
call :print_header "🚀 Starting FloraGuard AI Services..."

REM Check if .env has been configured
findstr /C:"your_gemini_api_key_here" .env >nul
if not errorlevel 1 (
    call :print_error "Please configure your .env file with actual API keys before starting services"
    call :print_status "Edit .env file and replace 'your_gemini_api_key_here' with your actual Gemini API key"
    pause
    exit /b 1
)

REM Start Redis
call :start_redis

call :print_status "Starting backend service..."
cd backend
start /B cmd /c "backend_venv\Scripts\activate.bat && python -c \"import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)\" > backend.log 2>&1"
cd ..

timeout /t 5 >nul

call :print_status "Starting frontend service..."
cd web_app
start /B cmd /c "web_venv\Scripts\activate.bat && streamlit run app.py --server.port 8502 > frontend.log 2>&1"
cd ..

timeout /t 5 >nul

REM Check if services are running
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    call :print_warning "Backend service may still be starting..."
    timeout /t 5 >nul
    curl -s http://localhost:8001/health >nul 2>&1
    if errorlevel 1 (
        call :print_error "Backend service failed to start. Check backend.log"
        pause
        exit /b 1
    )
)
call :print_status "Backend service started successfully ✅"

curl -s http://localhost:8502 >nul 2>&1
if errorlevel 1 (
    call :print_warning "Frontend service may still be starting..."
    timeout /t 5 >nul
    curl -s http://localhost:8502 >nul 2>&1
    if errorlevel 1 (
        call :print_error "Frontend service failed to start. Check frontend.log"
        pause
        exit /b 1
    )
)
call :print_status "Frontend service started successfully ✅"

call :print_header "🎉 FloraGuard AI is now running!"
echo.
echo 📱 Web Interface: http://localhost:8502
echo 🔧 API Documentation: http://localhost:8001/docs
echo ❤️ Health Check: http://localhost:8001/health
echo.
echo To stop services, run: setup.bat stop
echo Press any key to open the web interface...
pause >nul
start http://localhost:8502
goto :eof

REM Function to stop services
:stop_services
call :print_header "🛑 Stopping FloraGuard AI Services..."

REM Kill backend
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main:app*" >nul 2>&1
call :print_status "Backend service stopped"

REM Kill frontend
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *streamlit*" >nul 2>&1
call :print_status "Frontend service stopped"

call :print_status "All services stopped ✅"
goto :eof

REM Function to show status
:show_status
call :print_header "📊 FloraGuard AI Status"

REM Check Redis
tasklist /FI "IMAGENAME eq redis-server.exe" 2>NUL | find /I /N "redis-server.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Redis: %GREEN%Running%NC%
) else (
    echo Redis: %RED%Stopped%NC%
)

REM Check Backend
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (
    echo Backend: %RED%Stopped%NC%
) else (
    echo Backend: %GREEN%Running%NC% (http://localhost:8001)
)

REM Check Frontend
curl -s http://localhost:8502 >nul 2>&1
if errorlevel 1 (
    echo Frontend: %RED%Stopped%NC%
) else (
    echo Frontend: %GREEN%Running%NC% (http://localhost:8502)
)
goto :eof

REM Main script logic
if "%1"=="" goto setup
if "%1"=="setup" goto setup
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="status" goto status
if "%1"=="restart" goto restart
goto usage

:setup
call :print_header "🌿 FloraGuard AI - Complete Windows Setup"
call :check_python
call :check_redis
call :setup_env
call :setup_backend
call :setup_frontend
call :print_header "✅ Setup completed successfully!"
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: setup.bat start
pause
goto :eof

:start
call :start_services
goto :eof

:stop
call :stop_services
goto :eof

:status
call :show_status
goto :eof

:restart
call :stop_services
timeout /t 2 >nul
call :start_services
goto :eof

:usage
echo Usage: %0 {setup^|start^|stop^|status^|restart}
echo.
echo Commands:
echo   setup   - Install dependencies and setup environment
echo   start   - Start all services
echo   stop    - Stop all services
echo   status  - Show service status
echo   restart - Restart all services
pause
exit /b 1