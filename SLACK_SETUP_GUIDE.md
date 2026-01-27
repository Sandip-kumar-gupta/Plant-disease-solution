# 🚀 Slack Integration Setup Guide

## 📋 Prerequisites
- Slack workspace admin access
- FloraGuard backend running
- Redis server active

## 🔧 Step-by-Step Slack Setup

### 1. Create Slack App
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. App Name: `FloraGuard AI`
5. Select your workspace
6. Click **"Create App"**

### 2. Configure Bot Permissions
1. In your app dashboard, go to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** section
3. Add these **Bot Token Scopes**:
   - `chat:write` - Send messages
   - `chat:write.public` - Send messages to public channels
   - `channels:read` - View basic channel info
   - `groups:read` - View private channel info

### 3. Install App to Workspace
1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

### 4. Create Alert Channel
1. In Slack, create a new channel: `#plant-alerts`
2. Invite the FloraGuard bot: `/invite @FloraGuard AI`

### 5. Update Environment Variables
```bash
# Add to your .env file
SLACK_BOT_TOKEN=xoxb-your-copied-token-here
SLACK_CHANNEL=#plant-alerts
```

### 6. Restart Backend
```bash
# Stop and restart backend to load new token
cd backend
./backend_venv/bin/python -c "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8001, reload=True)"
```

## 🧪 Test Integration
```bash
# Test reminder creation
curl -X POST http://localhost:8001/reminder \
  -H "Content-Type: application/json" \
  -d '{
    "medication": "Test Fungicide",
    "dosage": "5ml per liter", 
    "frequency": "Daily",
    "disease": "Test Disease"
  }'
```

## ✅ Verification
- Check `#plant-alerts` channel for test message
- Backend logs should show "Slack alert sent"
- No error messages in console

## 🔧 Troubleshooting
- **Token Error**: Verify token starts with `xoxb-`
- **Permission Error**: Check bot has `chat:write` scope
- **Channel Error**: Ensure bot is invited to channel
- **Network Error**: Check firewall/proxy settings