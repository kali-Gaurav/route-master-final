# 🚀 FINALTrip Live Deployment - Quick Commands

**Just copy & paste these commands to deploy in 30 minutes!**

---

## ✅ Step 1: Prepare Your Repo (5 minutes)

```bash
# Navigate to project directory
cd "C:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final"

# Verify deployment files exist
dir Procfile requirements.txt .env.production .gitattributes production.db

# Verify all files have content
type Procfile
type requirements.txt | findstr gunicorn
type .env.production | findstr FLASK_ENV
```

**Expected Output**:
- ✅ All 4 files should exist
- ✅ `requirements.txt` should contain `gunicorn==21.2.0`
- ✅ `.env.production` should have configuration

---

## ✅ Step 2: Push to GitHub (3 minutes)

```bash
# Check git status
git status

# Stage deployment files
git add Procfile requirements.txt .env.production .gitattributes

# Commit
git commit -m "Prepare for free-tier live deployment (Vercel + Render)"

# Push to GitHub
git push origin main

# Verify
git log --oneline -5
```

**Expected**: Last commit should show deployment files added

---

## ✅ Step 3: Deploy Frontend to Vercel (10 minutes)

### Manual Steps (Easiest):

1. **Open** https://vercel.com/new
2. **Connect GitHub** and authorize
3. **Import Project**: Select your GitHub repo
4. **Configure**:
   - Framework: Vite (auto-selected)
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. **Environment Variables**:
   - Add variable:
     - Name: `VITE_API_URL`
     - Value: `https://localhost:5000` (temporary)
     - All Environments: checked
6. **Deploy** button

**Wait** 1-2 minutes for Vercel to build...

**Result**: You'll get a URL like `https://yourname-finaltrip.vercel.app`

### Using Vercel CLI (Advanced):

```bash
# Install CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod

# Add environment variables
vercel env add VITE_API_URL https://localhost:5000 production
```

---

## ✅ Step 4: Deploy Backend to Render (10 minutes)

### Manual Steps (Easiest):

1. **Open** https://dashboard.render.com
2. **Sign Up** with GitHub (authorize)
3. **New +** → **Web Service**
4. **Connect Repository**: Select your repo
5. **Configure**:
   - Name: `finaltrip-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn api:app`
   - Plan: **Free** (Important!)
6. **Environment** tab - Add these variables:

```
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=<PASTE_GENERATED_KEY_HERE>
CORS_ORIGINS=https://yourname-finaltrip.vercel.app
DATABASE_URL=sqlite:///production.db
```

### Generate SECRET_KEY:

```bash
# Run in PowerShell
python -c "import secrets; print(secrets.token_hex(32))"

# Example output: a1b2c3d4e5f6... (copy this)
```

**Copy the output** and paste as `SECRET_KEY` value.

7. **Deploy** button

**Wait** 3-5 minutes for Render to build and deploy...

**Result**: You'll get a URL like `https://finaltrip-api.onrender.com`

---

## ✅ Step 5: Connect Frontend to Backend (5 minutes)

### Update Vercel:

1. **Go to** https://vercel.com/yourname/finaltrip
2. **Settings** → **Environment Variables**
3. **Edit** `VITE_API_URL`:
   - Change from: `https://localhost:5000`
   - Change to: `https://finaltrip-api.onrender.com`
4. **Deployments** tab
5. **Click** latest deployment → **Redeploy**

**Wait** 1 minute for rebuild...

### Update Render:

1. **Go to** https://dashboard.render.com/web/srv-...
2. **Environment** tab
3. **Edit** `CORS_ORIGINS`:
   - Change to: `https://yourname-finaltrip.vercel.app`
4. Save (auto-redeploys in <1 min)

---

## ✅ Step 6: Test Everything (5 minutes)

```bash
# Test 1: Frontend is online
curl https://yourname-finaltrip.vercel.app

# Test 2: Backend is online
curl https://finaltrip-api.onrender.com/api/health

# Test 3: API endpoint works
curl "https://finaltrip-api.onrender.com/api/routes?origin=CSMT&destination=DADA"
```

**Or just open in browser**:
```
https://yourname-finaltrip.vercel.app
```

Try searching for a route!

---

## 📋 Complete Checklist

```bash
# Check all deployment files exist
✅ Procfile
✅ requirements.txt (has gunicorn)
✅ .env.production
✅ .gitattributes
✅ production.db

# GitHub
✅ Code pushed to main branch
✅ All 4 files committed

# Vercel
✅ Project created and built
✅ VITE_API_URL set to Render URL
✅ Domain shows as deployed

# Render
✅ Web Service created and built
✅ All environment variables set
✅ GREEN indicator shows service running

# Integration
✅ Frontend can reach backend
✅ No CORS errors
✅ Routes appear in search results
✅ All features work
```

---

## 🆘 Troubleshooting Commands

### Check if files are in GitHub:

```bash
# List files in repo
git ls-files | grep -E "(Procfile|requirements|\.env|\.gitattributes|production.db)"

# Check if Procfile has right content
git show HEAD:Procfile
```

### Check requirements.txt has gunicorn:

```bash
grep -i gunicorn requirements.txt

# Should output: gunicorn==21.2.0
```

### Check production.db is tracked:

```bash
# Should show production.db
git lfs ls-files

# Or check git attributes
git check-attr filter production.db
```

### Reset and retry:

```bash
# If something went wrong, reset and retry
git reset --hard HEAD~1
git clean -fd

# Then repeat steps 2-5
```

---

## 🎯 Your URLs (Update These)

```
Frontend: https://yourname.vercel.app
Backend: https://finaltrip-api.onrender.com

# Example (for reference only):
Frontend: https://gaurav-finaltrip.vercel.app
Backend: https://finaltrip-api-gaurav.onrender.com
```

---

## ⏱️ Total Time Required

| Task | Time | Status |
|------|------|--------|
| Step 1: Prepare Repo | 5 min | ⏱️ |
| Step 2: Push GitHub | 3 min | ⏱️ |
| Step 3: Deploy Frontend | 10 min | ⏱️ |
| Step 4: Deploy Backend | 10 min | ⏱️ |
| Step 5: Connect | 5 min | ⏱️ |
| Step 6: Test | 5 min | ⏱️ |
| **TOTAL** | **38 min** | ✅ |

**You can be live in under 1 hour!**

---

## 📱 Share Your Live Website

Once deployed:

```
Share this link:
https://yourname.vercel.app

Try searching for trains:
- CSMT to DADA
- NDLS to KOTA
- CSMT to RAJKOT

The website is now LIVE! 🎉
```

---

## 🚀 You're Ready!

All files are prepared. All setup is done. Just follow these 6 steps and you'll be live in 30 minutes!

**The hardest part is done** - the last 30 minutes is just clicking buttons and pasting URLs.

**Let's go!** 🚀

---

**Last Updated**: January 26, 2026  
**Status**: Ready to Deploy  
**Expected Outcome**: Live website in production  
