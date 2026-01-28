# Environment Variable Setup Guide

This guide explains how to configure environment variables for development and production deployment.

## 📝 Files for Configuration

- **Development**: Create `.env` file (not in Git)
- **Production**: Use `.env.production` (template provided)
- **Reference**: Check `.env.example` for all available variables

---

## 🔧 Development Setup (.env)

Create a `.env` file in your `route-master-final/` directory:

```bash
cat > .env << 'EOF'
# Development Environment
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production

# Database (Local)
DATABASE_URL=sqlite:///production.db
DATABASE_PATH=production.db

# API Configuration
API_PORT=5000
API_HOST=0.0.0.0

# CORS (Allow localhost:5173 for React dev server)
CORS_ORIGINS=http://localhost:5173,http://localhost:5000

# RAPPID API (Optional)
RAPPID_API_KEY=your_api_key_here
RAPPID_API_HOST=rappid.co.in

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/development.log

# Cache
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=3600
EOF
```

Then load it:
```bash
source .env  # On Windows: .\.env (PowerShell) or set /p ... (CMD)
python api.py
```

---

## 🚀 Production Setup (Vercel + Render)

### 1. Frontend Environment Variables (Vercel)

**In Vercel Dashboard**:
1. Select your project
2. Settings → Environment Variables
3. Add these variables:

```
Name: VITE_API_URL
Value: https://finaltrip-api.onrender.com
Environment: Production, Preview, Development
```

**Optional** (for analytics):
```
Name: VITE_GTAG_ID
Value: G-XXXXXXXXXX  (Your Google Analytics ID)
Environment: Production
```

---

### 2. Backend Environment Variables (Render)

**In Render Dashboard**:
1. Select your `finaltrip-api` service
2. Environment tab
3. Add these variables:

```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<generate-random-key>
CORS_ORIGINS=https://yourname-finaltrip.vercel.app
DATABASE_URL=sqlite:///production.db
DATABASE_PATH=production.db
FLASK_LOG_LEVEL=WARNING
LOG_FILE=/tmp/api.log
```

**Generate SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 🔐 Environment Variables Reference

### Flask Configuration

| Variable | Development | Production | Required |
|----------|-------------|------------|----------|
| `FLASK_ENV` | `development` | `production` | Yes |
| `FLASK_DEBUG` | `1` | `0` | Yes |
| `SECRET_KEY` | `dev-key` | Random 32-char | Yes |
| `FLASK_LOG_LEVEL` | `DEBUG` | `WARNING` | No |

### Database Configuration

| Variable | Development | Production | Required |
|----------|-------------|------------|----------|
| `DATABASE_URL` | `sqlite:///production.db` | Same | Yes |
| `DATABASE_PATH` | `production.db` | Same | No |

### API Configuration

| Variable | Development | Production | Required |
|----------|-------------|------------|----------|
| `API_PORT` | `5000` | N/A (Render sets it) | No |
| `API_HOST` | `0.0.0.0` | `0.0.0.0` | No |

### CORS Configuration

| Variable | Value | Notes |
|----------|-------|-------|
| `CORS_ORIGINS` | Development: `http://localhost:5173,http://localhost:5000` | Multiple values separated by commas |
| `CORS_ORIGINS` | Production: `https://yourname-finaltrip.vercel.app` | Exact domain with https:// |

### RAPPID API (Optional)

| Variable | Example | Notes |
|----------|---------|-------|
| `RAPPID_API_KEY` | `abc123def456` | Get from RAPPID dashboard |
| `RAPPID_API_HOST` | `rappid.co.in` | API hostname |
| `RAPPID_BASE_URL` | `https://api.rappid.co.in` | Full API URL |

### Logging

| Variable | Development | Production | Notes |
|----------|-------------|------------|-------|
| `LOG_LEVEL` | `DEBUG` | `INFO` | Verbosity level |
| `LOG_FILE` | `logs/development.log` | `/tmp/api.log` | File path |

### Cache Configuration

| Variable | Value | Notes |
|----------|-------|-------|
| `CACHE_TYPE` | `simple` | In-memory cache |
| `CACHE_DEFAULT_TIMEOUT` | `3600` | 1 hour in seconds |

---

## 🎯 Common Environment Setups

### Setup 1: Local Development

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=1
CORS_ORIGINS=http://localhost:5173,http://localhost:5000
DATABASE_URL=sqlite:///production.db
LOG_LEVEL=DEBUG
```

**Result**: Full debugging, hot reload, CORS allows localhost

### Setup 2: Production (Free Tier)

```bash
# Vercel Environment Variables
VITE_API_URL=https://finaltrip-api.onrender.com

# Render Environment Variables
FLASK_ENV=production
FLASK_DEBUG=0
CORS_ORIGINS=https://yourname-finaltrip.vercel.app
SECRET_KEY=<random-32-char-key>
LOG_LEVEL=INFO
```

**Result**: Secure, optimized, CORS restricted to your domain

### Setup 3: Production (Custom Domain)

```bash
# Vercel Environment Variables
VITE_API_URL=https://api.yourdomain.com

# Render Environment Variables
FLASK_ENV=production
CORS_ORIGINS=https://www.yourdomain.com,https://yourdomain.com
```

**Result**: Professional URLs with custom domain

---

## ⚙️ How to Set Variables

### Development (Local Machine)

**Option 1: Using .env file**
```bash
# Create .env file
nano .env
# Add variables, save with Ctrl+X

# Load and run
python api.py  # Automatically loads .env
```

**Option 2: Using Command Line**
```bash
# Linux/Mac
export FLASK_ENV=production
python api.py

# Windows PowerShell
$env:FLASK_ENV="production"
python api.py

# Windows CMD
set FLASK_ENV=production
python api.py
```

### Production (Vercel)

1. Go to dashboard
2. Select project → Settings
3. Environment Variables
4. Click "Add" for each variable
5. Redeploy to apply changes

### Production (Render)

1. Go to dashboard
2. Select service
3. Environment tab
4. Add or edit variables
5. Service auto-redeploys within 1 minute

---

## 🔍 Verify Your Variables

### Check if .env is loaded (Python)

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Check variables
print(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"CORS_ORIGINS: {os.getenv('CORS_ORIGINS')}")
```

### Check Vercel variables

1. Vercel Dashboard → Project → Settings → Environment Variables
2. You should see all variables listed

### Check Render variables

1. Render Dashboard → Service → Environment
2. Variables should be visible

---

## 🚨 Troubleshooting

### "No module named dotenv"
```bash
pip install python-dotenv
```

### Variables not being loaded

**Check 1**: Is `.env` in the correct directory?
```bash
ls -la .env  # Should exist in route-master-final/
```

**Check 2**: Is `.env` in `.gitignore`?
```bash
grep "\.env" .gitignore  # Should be there (don't commit secrets!)
```

**Check 3**: Load it explicitly in Python
```python
from dotenv import load_dotenv
load_dotenv()  # Load from .env
```

### "CORS errors" after deployment

**Cause**: `CORS_ORIGINS` doesn't match your frontend URL
**Solution**: 
1. Get exact Vercel URL
2. Update `CORS_ORIGINS` in Render to match exactly
3. Wait 60 seconds for redeploy

**Example**:
```
Vercel URL: https://my-app-yzxwvu.vercel.app
CORS_ORIGINS: https://my-app-yzxwvu.vercel.app  # Must match exactly!
```

---

## 📚 Best Practices

✅ **DO**:
- Keep `.env` file local (don't commit to Git)
- Use different keys for dev/prod
- Use strong random SECRET_KEY in production
- Rotate SECRET_KEY periodically
- Log environment on startup

❌ **DON'T**:
- Commit `.env` to Git repository
- Use same SECRET_KEY everywhere
- Hardcode sensitive values in code
- Share `.env` file in Slack/email
- Use `123456` as SECRET_KEY

---

## 🔐 Security Tips

### Generate Secure Keys

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Generate API Key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Environment Variable Rotation

Update `SECRET_KEY` every 90 days:
```bash
# Generate new key
python -c "import secrets; print(secrets.token_hex(32))"

# Update in Render Dashboard
# All sessions will be invalidated (users need to re-login)
```

---

## 📋 Deployment Environment Checklist

Before deploying, verify all variables are set:

- [ ] `FLASK_ENV=production`
- [ ] `FLASK_DEBUG=0`
- [ ] `SECRET_KEY=<32-char-random-key>`
- [ ] `CORS_ORIGINS=<your-exact-vercel-domain>`
- [ ] `DATABASE_URL=sqlite:///production.db`
- [ ] `LOG_LEVEL=INFO` (not DEBUG)
- [ ] All API keys set (RAPPID_API_KEY, etc.)

---

**Last Updated**: January 26, 2026  
**Status**: Ready for Production ✅
