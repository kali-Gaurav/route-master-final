# Vercel Deployment - Files & Architecture

## 🔄 How Vercel Deploys This Project

### What Vercel Uses From Your Repository:

```
route-master-final/
│
├── 📦 VERCEL WILL USE:
│   ├── package.json ...................... Detect dependencies & build commands
│   ├── vercel.json ....................... Read deployment configuration
│   ├── vite.config.ts .................... Build frontend (via npm run build)
│   ├── src/ ............................. Source files for Vite
│   ├── api/index.py ..................... Serverless Python function
│   ├── api/requirements.txt .............. Python dependencies
│   ├── tailwind.config.ts ............... CSS framework config
│   ├── tsconfig.json .................... TypeScript config
│   └── public/ .......................... Static assets
│
├── 📝 VERCEL WILL READ (config only):
│   ├── .env files (if public) ........... Environment reference
│   └── .vercelignore .................... Files to exclude
│
└── 🚫 VERCEL WILL IGNORE:
    ├── .git/ ........................... (git history)
    ├── node_modules/ ................... (will reinstall)
    ├── .venv/, venv/ ................... (will reinstall)
    ├── dist/ (initially) ............... (will regenerate)
    ├── README.md, docs/ ................ (documentation)
    ├── test/, tests/ ................... (test files)
    ├── .gitignore, .env.example ........ (reference files)
    └── Various other non-essential files
```

---

## 📋 Build Steps Vercel Performs

### Step 1: Install Dependencies
```bash
# Vercel runs this command:
npm install --legacy-peer-deps

# From: package.json (dependencies)
# Installs:
# - React 18.3.1
# - React Router 6.30.1
# - Vite 7.3.1
# - TypeScript 5.8.3
# - Tailwind CSS 3.4.17
# - shadcn/ui components
# - And all dev dependencies
```

### Step 2: Build Frontend
```bash
# Vercel reads from vercel.json:
# "buildCommand": "npm run build"

# Which runs from package.json:
# "build": "vite build"

# Output Directory: dist/
# Creates:
# ├── dist/index.html
# ├── dist/assets/
# │   ├── index-*.js
# │   ├── index-*.css
# │   ├── vendor-*.js
# │   └── vendor-*.css
# └── dist/manifest.json
```

### Step 3: Install Python Dependencies
```bash
# Vercel reads from vercel.json:
# "functions": { "api/index.py": { "runtime": "python3.12" } }

# And from api/requirements.txt:
pip install -r api/requirements.txt

# Installs:
# - Flask 3.1.2
# - Flask-CORS 6.0.1
# - python-dotenv 1.0.1
# - Werkzeug 3.0.0
# - gunicorn 21.2.0
```

### Step 4: Prepare Deployment
```
Vercel prepares two deployment targets:

1. STATIC FRONTEND:
   /dist → CDN (cloudflare-edge)
   ├── index.html (served to /)
   ├── assets/ (1-year cache)
   └── static files

2. SERVERLESS FUNCTION:
   /api/index.py → Python 3.12 runtime
   ├── Memory: 512 MB
   ├── Timeout: 60 seconds
   ├── Cold start: 1-2s
   └── Warm start: <100ms
```

---

## 🗺️ Request Routing

### How Vercel Routes Requests:

```
Client Request
    ↓
Vercel Router (reads vercel.json "routes")
    ↓
    ├─ /api/* → api/index.py (Python Flask)
    │
    └─ /* → dist/index.html (React SPA)
```

### Example Request Paths:

```
GET https://app.vercel.app/
├─ Route Match: /* → dist/index.html
├─ Status: 200
└─ Response: React HTML with JS bundle

GET https://app.vercel.app/search
├─ Route Match: /* → dist/index.html (SPA routing)
├─ Status: 200
└─ Response: React Router handles internally

GET https://app.vercel.app/api/health
├─ Route Match: /api/* → api/index.py
├─ Status: 200
└─ Response: {"status": "healthy", "service": "Route Master API", "version": "1.0.0"}

POST https://app.vercel.app/api/routes
├─ Route Match: /api/* → api/index.py
├─ Method: POST with JSON body
├─ Status: 200
└─ Response: {"success": true, "routes": [...], "count": N}

GET https://app.vercel.app/assets/vendor-ui-*.js
├─ Route Match: /* → dist/assets/vendor-ui-*.js
├─ Status: 200
├─ Cache-Control: public, max-age=31536000, immutable
└─ Response: Minified JavaScript
```

---

## 📦 What Gets Deployed

### On Vercel's Servers:

```
vercel-deployment/
├── .vercel/
│   ├── output/
│   │   ├── static/
│   │   │   └── [dist files]
│   │   ├── functions/
│   │   │   └── api/index.py.func
│   │   └── config.json
│   └── project.json
│
├── .env (from secrets, not in repo)
└── [Other runtime files]

# What's NOT deployed:
- .git/
- node_modules/
- .venv/
- __pycache__/
- Test files
- Documentation
- Source maps (if disabled)
```

---

## 🔗 URL Structure After Deployment

```
https://your-project-name.vercel.app

├── / ........................... React App (dist/index.html)
├── /search ..................... React Router (dist/index.html)
├── /results/... ................ React Router (dist/index.html)
│
├── /api/health ................. Flask API
├── /api/routes ................. Flask API
├── /api/stations ............... Flask API
├── /api/route-details/:id ...... Flask API
├── /api/validate ............... Flask API
│
├── /assets/index-*.js .......... React + Vite code
├── /assets/index-*.css ......... Tailwind CSS
├── /assets/vendor-*.js ......... NPM packages
├── /assets/vendor-*.css ........ Package CSS
│
├── /favicon.ico ................ Static file
├── /manifest.json .............. PWA manifest
└── /robots.txt ................. SEO file
```

---

## 🔐 Environment Variables

### Set in Vercel Dashboard:

```
IRCTC_API_KEY = "your-rapid-api-key"
IRCTC_API_HOST = "irctc1.p.rapidapi.com"
IRCTC_BASE_URL = "https://irctc1.p.rapidapi.com/api/v3"
```

### Available in:
- `api/index.py` - Via `os.getenv('VARIABLE_NAME')`
- Frontend - Via `import.meta.env.VITE_VARIABLE_NAME` (only if prefixed with VITE_)

---

## 🚀 Deployment Timeline

```
t=0s   Git push to main
         ↓
t=5s   Vercel detects push
         ↓
t=10s  Vercel clones repository
         ↓
t=15s  npm install
         ↓
t=45s  npm run build (generates dist/)
         ↓
t=55s  pip install (api/ requirements)
         ↓
t=65s  Prepare serverless function
         ↓
t=75s  Deploy to CDN and serverless
         ↓
t=85s  ✅ Live at https://your-project.vercel.app
```

---

## 🎯 Critical Files for Vercel

### MUST EXIST (Deployment will fail without these):

```
✅ package.json
   - Must have "build" script
   - Must have "type": "module" or valid script format

✅ vercel.json
   - Must specify outputDirectory: "dist"
   - Must specify buildCommand
   - Routes must be defined
   
✅ api/index.py
   - Must be valid Python 3.12 code
   - Must export Flask app as `app`
   
✅ api/requirements.txt
   - Must list all Python dependencies
   - Must be readable
```

### SHOULD EXIST (Best practice):

```
✅ .vercelignore
   - Reduces deployment size
   - Speeds up deployment
   
✅ vite.config.ts
   - Ensures proper Vite configuration
   - Already configured in your project
```

### NICE TO HAVE (Optional):

```
.env.vercel
- Reference for environment variables
- Not deployed, just documentation

README.md
- Deployment instructions
- Setup guide for contributors
```

---

## 🔄 Update Cycle

### Each time you push to GitHub:

```
1. Vercel detects push
2. Runs npm install
3. Runs npm run build
4. Installs Python deps
5. Deploys new version
6. Previous version becomes rollback option

# You can rollback to any previous deployment
# from Vercel dashboard
```

---

## 📊 Deployment Diagram

```
┌─────────────────────────────────────────┐
│         Your GitHub Repository           │
│                                          │
│  - src/ (React code)                     │
│  - api/index.py (Flask)                  │
│  - package.json                          │
│  - vercel.json                           │
└────────────────────┬────────────────────┘
                     │
              (git push main)
                     │
┌────────────────────▼────────────────────┐
│      Vercel Platform (Detected)          │
│                                          │
│  1. Install dependencies                 │
│  2. Run: npm run build                   │
│  3. Generate: dist/                      │
│  4. Prepare: api/index.py                │
└────────────────────┬────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌─────▼────┐
    │ Frontend  │          │ Backend   │
    │ Static    │          │ Serverless│
    │ (Vercel   │          │ (Python   │
    │  CDN)     │          │  3.12)    │
    │           │          │           │
    │ dist/     │          │ api/      │
    │ → CDN     │          │ index.py  │
    │ (cached)  │          │ → function│
    └────┬──────┘          └─────┬────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────▼───────────┐
         │                       │
    https://your-project.vercel.app
         │                       │
    ┌────▼─────────────────┬────▼────┐
    │ Frontend             │ Backend  │
    │ (Fast CDN)           │ (Scaled) │
    │ Load time: <1s       │ <500ms   │
    │ (98% cached)         │ (dynamic)│
    └──────────────────────┴──────────┘
```

---

## ✅ Pre-Deployment Checklist

```
□ api/index.py exists ........................ CRITICAL
□ api/requirements.txt exists ............... CRITICAL
□ vercel.json exists ........................ CRITICAL
□ package.json has build script ............. CRITICAL

□ npm run build produces dist/ .............. REQUIRED
□ dist/index.html exists ................... REQUIRED
□ dist/assets/ has JS/CSS files ............ REQUIRED

□ Python code syntax is valid .............. RECOMMENDED
□ .vercelignore exists ..................... RECOMMENDED
□ Environment variables documented ......... RECOMMENDED

□ All imports in api/index.py work ......... NICE TO HAVE
□ Static assets have proper paths .......... NICE TO HAVE
□ CORS is properly configured .............. NICE TO HAVE
```

---

**Last Updated:** 2026-01-26
**Status:** ✅ Ready for Vercel Deployment
**Vercel Runtime:** Python 3.12 + Node.js (Vite)
