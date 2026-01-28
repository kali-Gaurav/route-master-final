# FINALTrip - Free-Tier Deployment Guide (2026)

**Goal**: Deploy the FINALTrip website completely free using Vercel (Frontend) + Render (Backend)

---

## 📋 Pre-Deployment Checklist

Before starting, ensure you have:
- [ ] GitHub account (free)
- [ ] Code pushed to GitHub repository
- [ ] `production.db` file in your repo root
- [ ] `Procfile` file in your repo root (already created ✅)
- [ ] `requirements.txt` updated with gunicorn (already done ✅)
- [ ] `.env.production` configured (already created ✅)

---

## 🚀 Step 1: Deploy Frontend to Vercel (10 minutes)

### 1.1 Prepare Frontend for Production

Update your `.env` file for production API endpoint:

```bash
# .env or .env.production
VITE_API_URL=https://your-backend-url.onrender.com
```

Push to GitHub:
```bash
git add .env.production vite.config.ts package.json
git commit -m "Production configuration for Vercel deployment"
git push origin main
```

### 1.2 Deploy to Vercel

1. **Go to** [vercel.com](https://vercel.com)
2. **Click** "New Project"
3. **Connect** your GitHub repository (select `route-master-final` or your repo name)
4. **Configure Build Settings**:
   - Framework: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

5. **Add Environment Variables**:
   - Name: `VITE_API_URL`
   - Value: `https://your-backend-url.onrender.com` (you'll update this after backend deployment)

6. **Click** "Deploy"

**Result**: Your frontend will be available at `https://yourname-finaltrip.vercel.app`

---

## 🚀 Step 2: Deploy Backend to Render (15 minutes)

### 2.1 Prepare Backend for Production

Ensure these files exist in your root directory:

**Procfile** (already created ✅):
```
web: gunicorn api:app
```

**requirements.txt** (already updated ✅):
```
flask==2.3.0
flask-cors==4.0.0
gunicorn==21.2.0
pandas==2.0.0
numpy==1.24.0
... (all dependencies)
```

**.env.production** (already created ✅):
```
FLASK_ENV=production
CORS_ORIGINS=https://yourname-finaltrip.vercel.app
DATABASE_URL=sqlite:///production.db
```

**Important**: Add `production.db` to Git LFS (large files):
```bash
git lfs install
git lfs track "*.db"
git add .gitattributes
git commit -m "Track large database file with Git LFS"
git push origin main
```

### 2.2 Deploy to Render

1. **Go to** [render.com](https://render.com)
2. **Sign Up** with GitHub (free)
3. **Click** "New +" → "Web Service"
4. **Connect** your GitHub repository
5. **Configure**:
   - **Name**: `finaltrip-api`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn api:app`
   - **Plan**: Free

6. **Add Environment Variables**:
   ```
   FLASK_ENV=production
   CORS_ORIGINS=https://yourname-finaltrip.vercel.app
   DATABASE_URL=sqlite:///production.db
   ```

7. **Click** "Create Web Service"

**Result**: Your backend will be available at `https://finaltrip-api.onrender.com`

**Note**: Render free tier starts your service in ~30 seconds. Your first request might take 10-15 seconds as it spins up.

---

## 🔗 Step 3: Connect Frontend & Backend

### 3.1 Update Vercel Environment Variable

1. **Go to** Vercel dashboard
2. **Select** your FINALTrip project
3. **Settings** → **Environment Variables**
4. **Update** `VITE_API_URL`:
   - Old: `https://localhost:5000`
   - New: `https://finaltrip-api.onrender.com`
5. **Re-deploy**:
   - Go to "Deployments"
   - Click "Redeploy" on the latest deployment

### 3.2 Update Render Environment Variable

1. **Go to** Render dashboard
2. **Select** your `finaltrip-api` web service
3. **Environment** tab
4. **Update** `CORS_ORIGINS`:
   - New: `https://yourname-finaltrip.vercel.app`
5. Service will automatically re-deploy

### 3.3 Test the Connection

**In your browser**, go to:
```
https://yourname-finaltrip.vercel.app
```

Try searching for a route (e.g., CSMT → DADA). If it works, you're live! 🎉

---

## 🗄️ Step 4: Database Strategy

### Option A: SQLite in Git (Simplest, Recommended)

✅ **Pros**:
- No database setup required
- Data persists across deployments
- Works immediately

❌ **Cons**:
- Limited to 100 MB file size
- Read-only in free tier
- Can't update data without redeploying

**Setup**:
```bash
# Track production.db with Git LFS
git lfs install
git lfs track "*.db"
git add .gitattributes production.db
git commit -m "Add production database"
git push origin main
```

### Option B: PostgreSQL with Supabase (Advanced)

If you need live data updates:

1. **Go to** [supabase.com](https://supabase.com)
2. **Sign Up** (free PostgreSQL database included)
3. **Create** a new project
4. **Update** your `database_manager.py`:
   ```python
   import os
   from sqlalchemy import create_engine
   
   # Change from SQLite to PostgreSQL
   database_url = os.getenv(
       'DATABASE_URL',
       'postgresql://user:password@host:port/database'
   )
   engine = create_engine(database_url)
   ```

5. **Update** `.env.production`:
   ```
   DATABASE_URL=postgresql://user:password@db.xxx.supabase.co:5432/postgres
   ```

6. **Migrate** your data:
   ```bash
   python -c "from database_manager import Base; Base.metadata.create_all()"
   ```

---

## 🐛 Troubleshooting

### "CORS Error" or "Access-Control-Allow-Origin"

**Problem**: Frontend can't reach backend API
**Solution**:
1. Check backend URL is correct in Vercel environment variable
2. Verify Render has your Vercel URL in `CORS_ORIGINS`
3. Wait 60 seconds for environment variables to apply
4. Hard refresh browser (Cmd+Shift+R)

### "No routes found" or Empty results

**Problem**: Database not loading or queries failing
**Solution**:
1. Check `production.db` file size (should be ~15 MB)
2. Verify database file is committed to Git with LFS
3. Render might need `production.db` file in build directory:
   ```bash
   # Add to build script if needed
   cp production.db /opt/render/project/src/
   ```

### Backend taking too long to respond

**Problem**: First request slow or timeout
**Reason**: Render free tier spins down after 15 minutes of inactivity
**Solution**:
1. Create a simple uptime monitor: [uptimerobot.com](https://uptimerobot.com)
2. Set to ping your backend every 5 minutes
3. Or upgrade to Render's paid tier ($7/month)

### "No space left on device"

**Problem**: Database file is too large
**Reason**: Render free tier has limited storage
**Solution**:
1. Clean temporary files: `python cleanup.py`
2. Compress older logs
3. Or move to Supabase PostgreSQL (Option B)

---

## ✅ Verification Checklist

Once deployed, verify everything works:

- [ ] Frontend loads at `https://yourname-finaltrip.vercel.app`
- [ ] Backend API responds at `https://finaltrip-api.onrender.com/api/health`
- [ ] Can search for routes (e.g., CSMT → DADA)
- [ ] Station autocomplete works
- [ ] Route cards display with categories (⚡💰🛡️ etc.)
- [ ] "Load More" pagination works
- [ ] Loading skeleton appears during search

**Test API endpoint directly**:
```bash
curl "https://finaltrip-api.onrender.com/api/routes?origin=CSMT&destination=DADA"
```

Should return JSON with routes.

---

## 🔒 Production Security

### Before Going Public

1. **Update Flask Secret Key**:
   ```bash
   # Generate random key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   
   Add to Render environment variables:
   ```
   SECRET_KEY=your-generated-key-here
   ```

2. **Enable HTTPS** (Vercel & Render do this automatically ✅)

3. **Set Production Environment**:
   ```
   FLASK_ENV=production
   FLASK_DEBUG=0
   ```

4. **Restrict CORS** to your domain:
   ```
   CORS_ORIGINS=https://yourname-finaltrip.vercel.app
   ```

5. **Monitor Logs**:
   - Vercel: Deployments → Logs
   - Render: Logs tab on your service

---

## 📊 Monitoring & Logs

### Vercel Logs
- **Settings** → **Real-time Logs**
- See frontend build/deploy issues

### Render Logs
- **Logs** tab on your service
- See backend errors in real-time

### Example: Monitor API response time
```bash
# Every 5 minutes
while true; do
  time curl -s "https://finaltrip-api.onrender.com/api/health" > /dev/null
  sleep 300
done
```

---

## 🚀 Next Steps (Optional Upgrades)

Once live and working on free tier:

1. **Upgrade Render** ($7/month) for:
   - Always-on service (no spin-down)
   - More memory
   - Database backup

2. **Add Custom Domain**:
   - Buy domain (namecheap.com, godaddy.com)
   - Point to Vercel (frontend) via DNS
   - Use subdomain `api.yourdomain.com` for Render

3. **Enable Analytics**:
   - Vercel Web Analytics (free)
   - Plausible Analytics or Posthog (privacy-focused)

4. **Set Up Monitoring**:
   - Sentry for error tracking (free tier)
   - UptimeRobot for uptime monitoring (free)

---

## 📞 Support

**Common Issues**:

| Issue | Solution |
|-------|----------|
| Blank page | Check browser console for errors, verify API URL in .env |
| CORS error | Ensure Render has correct CORS_ORIGINS set |
| Slow backend | Free tier spins down after 15 min, set uptime monitor |
| Database not found | Check `production.db` is in Git, use LFS if large |
| "Bad Gateway" | Backend crashed, check Render logs |

---

## 🎉 Congratulations! 🎉

Your FINALTrip website is now live on the internet, completely free!

**URLs**:
- Frontend: `https://yourname-finaltrip.vercel.app`
- Backend API: `https://finaltrip-api.onrender.com`
- API Health: `https://finaltrip-api.onrender.com/api/health`

**Share** with friends:
> "Check out my train route optimizer: https://yourname-finaltrip.vercel.app"

---

## 📝 Deployment Summary

| Component | Provider | Cost | Status |
|-----------|----------|------|--------|
| Frontend (React/Vite) | Vercel | Free | ✅ Live |
| Backend (Flask/Python) | Render | Free | ✅ Live |
| Database (SQLite) | GitHub | Free | ✅ Live |
| Domain | - | Free | 🔗 yourdomain.vercel.app |
| Total Cost | - | **$0** | 💚 |

---

**Document Version**: 1.0  
**Date**: January 26, 2026  
**Last Updated**: Deployment Guide  
**Next Step**: Share with users! 🚀
