# 🚀 FloraGuard AI - Deployment Guide

## 🎯 Quick Start (Recommended)

### 1. Clone Repository
```bash
git clone https://github.com/Raj-glitch-max/Plant-disease-solution.git
cd Plant-disease-solution
```

### 2. Run Setup Script
```bash
# Make setup script executable
chmod +x setup.sh

# Run complete setup
./setup.sh setup
```

### 3. Configure Environment
```bash
# Edit .env file with your API keys
nano .env

# Add your Gemini API key (required)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional: Add Slack bot token for notifications
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
```

### 4. Start Services
```bash
./setup.sh start
```

### 5. Access Application
- **Web Interface**: http://localhost:8502
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 🔧 Manual Setup (Advanced)

### Prerequisites
- Python 3.9+
- Redis Server
- 8GB RAM minimum
- Internet connection

### Backend Setup
```bash
cd backend
python3 -m venv backend_venv
source backend_venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd web_app
python3 -m venv web_venv
source web_venv/bin/activate
pip install -r requirements.txt
```

### Start Services Manually
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend
cd backend
source backend_venv/bin/activate
python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)"

# Terminal 3: Frontend
cd web_app
source web_venv/bin/activate
streamlit run app.py --server.port 8502
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Docker Containers
```bash
# Backend
cd backend
docker build -t floraguard-backend .
docker run -p 8001:8001 floraguard-backend

# Frontend
cd web_app
docker build -t floraguard-frontend .
docker run -p 8502:8502 floraguard-frontend
```

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (Redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Optional (Slack)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL=#plant-alerts
```

### Getting API Keys

#### Gemini API Key (Required)
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key to your .env file

#### Slack Bot Token (Optional)
1. Go to [Slack API](https://api.slack.com/apps)
2. Create new app → "From scratch"
3. Add bot scopes: `chat:write`, `chat:write.public`
4. Install to workspace
5. Copy Bot User OAuth Token

## 🧪 Testing Deployment

### Health Checks
```bash
# Backend health
curl http://localhost:8001/health

# Frontend accessibility
curl http://localhost:8502

# Redis connection
redis-cli ping
```

### Performance Test
```bash
# Test prediction endpoint
curl -X POST http://localhost:8001/predict \
  -F "file=@test_image.jpg"

# Test caching
curl http://localhost:8001/cache/stats
```

## 🔧 Service Management

### Using Setup Script
```bash
# Start all services
./setup.sh start

# Stop all services
./setup.sh stop

# Check status
./setup.sh status

# Restart services
./setup.sh restart
```

### Manual Service Management
```bash
# Stop backend
pkill -f "uvicorn.*main:app"

# Stop frontend
pkill -f "streamlit.*app.py"

# Stop Redis
redis-cli shutdown
```

## 📊 Monitoring & Logs

### Log Locations
```bash
# Backend logs
tail -f backend/backend.log

# Frontend logs
tail -f web_app/frontend.log

# Redis logs
tail -f /var/log/redis/redis-server.log
```

### Performance Monitoring
```bash
# System resources
htop

# Redis monitoring
redis-cli monitor

# API performance
curl http://localhost:8001/cache/stats
```

## 🔒 Security Configuration

### Production Security
```bash
# Set secure environment variables
export GEMINI_API_KEY="your-secure-key"
export SLACK_BOT_TOKEN="your-secure-token"

# Use HTTPS in production
# Configure reverse proxy (nginx/apache)
# Set up SSL certificates
```

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 8001  # Backend API
sudo ufw allow 8502  # Frontend
sudo ufw allow 6379  # Redis (internal only)
```

## 🚀 Production Deployment

### Cloud Deployment Options

#### AWS Deployment
```bash
# Using ECS/Fargate
aws ecs create-cluster --cluster-name floraguard-cluster

# Using EC2
# Launch EC2 instance
# Install Docker
# Deploy using docker-compose
```

#### Google Cloud Deployment
```bash
# Using Cloud Run
gcloud run deploy floraguard-backend --source backend/
gcloud run deploy floraguard-frontend --source web_app/
```

#### Azure Deployment
```bash
# Using Container Instances
az container create --resource-group floraguard-rg \
  --name floraguard-backend --image floraguard-backend
```

### Load Balancing
```bash
# Nginx configuration
upstream backend {
    server localhost:8001;
    server localhost:8002;  # Additional backend instances
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python3 --version

# Check dependencies
pip list

# Check logs
tail -f backend/backend.log
```

#### Frontend Connection Error
```bash
# Check backend health
curl http://localhost:8001/health

# Check network connectivity
netstat -tlnp | grep 8001
```

#### Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# Start Redis
redis-server --daemonize yes

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

#### Model Loading Error
```bash
# Check model files exist
ls -la android_app/app/src/main/assets/

# Check file permissions
chmod 644 android_app/app/src/main/assets/model.tflite
```

### Performance Issues

#### Slow Response Times
```bash
# Check system resources
htop

# Monitor Redis
redis-cli monitor

# Check cache hit rate
curl http://localhost:8001/cache/stats
```

#### Memory Issues
```bash
# Check memory usage
free -h

# Monitor Python processes
ps aux | grep python

# Restart services
./setup.sh restart
```

## 📞 Support

### Getting Help
- 📖 Check [README.md](README.md) for overview
- 🏗️ Review [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) for details
- 🔧 Follow [SLACK_SETUP_GUIDE.md](SLACK_SETUP_GUIDE.md) for notifications
- 🐛 Create GitHub issue for bugs

### System Requirements
- **Minimum**: 4GB RAM, 2GB storage, Python 3.9+
- **Recommended**: 8GB RAM, 5GB storage, Python 3.11+
- **Production**: 16GB RAM, 10GB storage, Load balancer

---

**🌿 FloraGuard AI - Ready for Production Deployment! 🚀**