#!/bin/bash

# FloraGuard AI - Setup Script
# This script sets up the complete FloraGuard AI system

set -e  # Exit on any error

echo "🌿 FloraGuard AI - Setup Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Python 3.9+ is installed
check_python() {
    print_header "🐍 Checking Python version..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
            print_status "Python $PYTHON_VERSION found ✅"
        else
            print_error "Python 3.9+ required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.9+"
        exit 1
    fi
}

# Check if Redis is installed
check_redis() {
    print_header "🔴 Checking Redis..."
    if command -v redis-server &> /dev/null; then
        REDIS_VERSION=$(redis-server --version | head -n1 | cut -d'=' -f2 | cut -d' ' -f1)
        print_status "Redis $REDIS_VERSION found ✅"
    else
        print_warning "Redis not found. Installing Redis..."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            brew install redis
        else
            print_error "Please install Redis manually for your OS"
            exit 1
        fi
    fi
}

# Setup environment file
setup_env() {
    print_header "⚙️ Setting up environment..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_status "Created .env file from template"
            print_warning "Please edit .env file with your API keys before running the system"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_status ".env file already exists"
    fi
}

# Setup backend
setup_backend() {
    print_header "🔧 Setting up Backend..."
    cd backend
    
    if [ ! -d "backend_venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv backend_venv
    fi
    
    print_status "Activating virtual environment..."
    source backend_venv/bin/activate
    
    print_status "Installing backend dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Backend setup complete ✅"
    cd ..
}

# Setup frontend
setup_frontend() {
    print_header "🎨 Setting up Frontend..."
    cd web_app
    
    if [ ! -d "web_venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv web_venv
    fi
    
    print_status "Activating virtual environment..."
    source web_venv/bin/activate
    
    print_status "Installing frontend dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_status "Frontend setup complete ✅"
    cd ..
}

# Start Redis
start_redis() {
    print_header "🚀 Starting Redis..."
    if pgrep redis-server > /dev/null; then
        print_status "Redis is already running"
    else
        print_status "Starting Redis server..."
        redis-server --daemonize yes
        sleep 2
        if pgrep redis-server > /dev/null; then
            print_status "Redis started successfully ✅"
        else
            print_error "Failed to start Redis"
            exit 1
        fi
    fi
}

# Function to start services
start_services() {
    print_header "🚀 Starting FloraGuard AI Services..."
    
    # Check if .env has been configured
    if grep -q "your_gemini_api_key_here" .env; then
        print_error "Please configure your .env file with actual API keys before starting services"
        print_status "Edit .env file and replace 'your_gemini_api_key_here' with your actual Gemini API key"
        exit 1
    fi
    
    # Start Redis
    start_redis
    
    print_status "Starting backend service..."
    cd backend
    source backend_venv/bin/activate
    nohup python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)" > backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    sleep 5
    
    print_status "Starting frontend service..."
    cd web_app
    source web_venv/bin/activate
    nohup streamlit run app.py --server.port 8502 > frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    sleep 5
    
    # Check if services are running
    if curl -s http://localhost:8001/health > /dev/null; then
        print_status "Backend service started successfully ✅"
    else
        print_error "Backend service failed to start"
        exit 1
    fi
    
    if curl -s http://localhost:8502 > /dev/null; then
        print_status "Frontend service started successfully ✅"
    else
        print_error "Frontend service failed to start"
        exit 1
    fi
    
    print_header "🎉 FloraGuard AI is now running!"
    echo ""
    echo "📱 Web Interface: http://localhost:8502"
    echo "🔧 API Documentation: http://localhost:8001/docs"
    echo "❤️ Health Check: http://localhost:8001/health"
    echo ""
    echo "To stop services, run: ./setup.sh stop"
}

# Function to stop services
stop_services() {
    print_header "🛑 Stopping FloraGuard AI Services..."
    
    # Kill backend
    pkill -f "uvicorn.*main:app" || true
    print_status "Backend service stopped"
    
    # Kill frontend
    pkill -f "streamlit.*app.py" || true
    print_status "Frontend service stopped"
    
    print_status "All services stopped ✅"
}

# Function to show status
show_status() {
    print_header "📊 FloraGuard AI Status"
    
    # Check Redis
    if pgrep redis-server > /dev/null; then
        echo -e "Redis: ${GREEN}Running${NC}"
    else
        echo -e "Redis: ${RED}Stopped${NC}"
    fi
    
    # Check Backend
    if curl -s http://localhost:8001/health > /dev/null; then
        echo -e "Backend: ${GREEN}Running${NC} (http://localhost:8001)"
    else
        echo -e "Backend: ${RED}Stopped${NC}"
    fi
    
    # Check Frontend
    if curl -s http://localhost:8502 > /dev/null; then
        echo -e "Frontend: ${GREEN}Running${NC} (http://localhost:8502)"
    else
        echo -e "Frontend: ${RED}Stopped${NC}"
    fi
}

# Main script logic
case "${1:-setup}" in
    "setup")
        print_header "🌿 FloraGuard AI - Complete Setup"
        check_python
        check_redis
        setup_env
        setup_backend
        setup_frontend
        print_header "✅ Setup completed successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Edit .env file with your API keys"
        echo "2. Run: ./setup.sh start"
        ;;
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "restart")
        stop_services
        sleep 2
        start_services
        ;;
    *)
        echo "Usage: $0 {setup|start|stop|status|restart}"
        echo ""
        echo "Commands:"
        echo "  setup   - Install dependencies and setup environment"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  status  - Show service status"
        echo "  restart - Restart all services"
        exit 1
        ;;
esac