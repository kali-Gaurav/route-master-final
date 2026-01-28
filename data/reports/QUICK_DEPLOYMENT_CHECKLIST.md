# FINALTrip Free Deployment - Quick Start Checklist

## 🎯 Your Deployment Timeline

**Current Status**: Code ready, infrastructure files prepared ✅

### Day 1: Setup & Deploy (2-3 hours)

- [ ] **Task 1**: Ensure `production.db` is in your repository root (should be ~15 MB)
- [ ] **Task 2**: Verify `Procfile` exists with content: `web: gunicorn api:app`
- [ ] **Task 3**: Verify `requirements.txt` includes `gunicorn==21.2.0`
- [ ] **Task 4**: Push everything to GitHub:
  ```bash
  cd route-master-final
  git add Procfile requirements.txt .env.production .gitattributes
  git commit -m "Prepare for free-tier deployment"
  git push origin main
  ```

- [ ] **Task 5**: Deploy Frontend to Vercel:
  1. Go to [vercel.com](https://vercel.com)
  2. Click "New Project"
  3. Select your GitHub repo
  4. Build Command: `npm run build`
  5. Output Directory: `dist`
  6. Add env var: `VITE_API_URL=https://localhost:5000` (temporary)
  7. Deploy! ✅

- [ ] **Task 6**: Deploy Backend to Render:
  1. Go to [render.com](https://render.com)
  2. Click "New Web Service"
  3. Select your GitHub repo
  4. Start Command: `gunicorn api:app`
  5. Add env var: `FLASK_ENV=production`
  6. Deploy! ✅
  7. **Copy backend URL** when it's deployed (format: `https://your-service-name.onrender.com`)

- [ ] **Task 7**: Connect Frontend to Backend:
  1. Go to Vercel project → Settings → Environment Variables
  2. Update `VITE_API_URL` to your Render backend URL
  3. Redeploy frontend

- [ ] **Task 8**: Update Backend CORS:
  1. Go to Render service → Environment
  2. Add `CORS_ORIGINS=https://your-vercel-app.vercel.app`
  3. Service auto-redeploys

- [ ] **Task 9**: Test the live website:
  1. Open `https://your-vercel-app.vercel.app`
  2. Try searching for a route (CSMT → DADA)
  3. Verify it works! 🎉

### Day 2: Monitor & Optimize (30 minutes)

- [ ] **Task 10**: Set up uptime monitoring (optional but recommended):
  - Go to [uptimerobot.com](https://uptimerobot.com)
  - Add monitor for your backend URL
  - Set interval to 5 minutes
  - This keeps Render from spinning down

- [ ] **Task 11**: Share your URL:
  - Post on social media
  - Share with friends: "Check out my train route optimizer! 🚂"
  - Get feedback

- [ ] **Task 12**: Set up basic analytics (optional):
  - Vercel has built-in Web Analytics (enable in Settings)
  - Google Analytics (add tracking code to index.html)

---

## 🔑 Key URLs After Deployment

**Replace `yourname` with your Vercel project name and `service-name` with your Render service name:**

```
Frontend: https://yourname-finaltrip.vercel.app
Backend API: https://finaltrip-api.onrender.com
API Endpoint: https://finaltrip-api.onrender.com/api/routes?origin=CSMT&destination=DADA
```

---

## ⚡ File Checklist (Required for Deployment)

Your repo should have these files in root:

- ✅ `Procfile` - Created
- ✅ `requirements.txt` - Updated with gunicorn
- ✅ `.env.production` - Created
- ✅ `.gitattributes` - Created
- ✅ `production.db` - Should already exist
- ✅ `api.py` - Updated with flexible CORS
- ✅ `vite.config.ts` - No changes needed

Run this to verify:
```bash
ls -la Procfile requirements.txt .env.production .gitattributes production.db
```

All should exist! ✅

---

## 🆘 If Something Goes Wrong

### Backend won't start
- **Check Logs**: Render → Logs tab
- **Common Error**: Missing `gunicorn` in requirements.txt (we already fixed this ✅)
- **Solution**: Verify requirements.txt has `gunicorn==21.2.0`

### Frontend shows blank page
- **Check Logs**: Browser Developer Tools (F12)
- **Common Error**: Wrong API URL in environment variable
- **Solution**: Ensure `VITE_API_URL` points to your Render backend

### "No routes found" in search
- **Check**: Is `production.db` actually in your Git repo?
- **Solution**: `git lfs track "*.db"` then commit it

### CORS errors in console
- **Check**: Backend's `CORS_ORIGINS` environment variable
- **Solution**: Set it to your exact Vercel URL (must match, no typos)

### Render backend takes 10-15 seconds to respond
- **Expected**: Free tier spins down after 15 min of inactivity
- **Solution**: Set up uptime monitor to ping every 5 min

---

## 💰 Cost Breakdown

| Service | Free Tier Limit | Cost | Notes |
|---------|-----------------|------|-------|
| Vercel Frontend | 100 GB bandwidth/month | $0 | Unlimited deployments |
| Render Backend | 750 hours/month | $0 | Spins down after 15 min inactivity |
| Database (SQLite) | 100 MB max file | $0 | Stored in Git |
| Domain | yourdomain.vercel.app | $0 | Included with Vercel |
| **TOTAL** | - | **$0** | ✅ Completely Free |

**Optional Upgrades** (if needed later):
- Render Pro: $7/month (always-on backend)
- Custom Domain: $12/year (buy from Namecheap/GoDaddy)
- PostgreSQL Database: $0-9/month (if using Supabase)

---

## 🚀 What Happens After Deployment

1. **Within 5 minutes**: Vercel builds and deploys your frontend
2. **Within 10 minutes**: Render starts your backend
3. **After 30 seconds**: Both services are "warm" and responsive
4. **After 15 minutes of inactivity**: Render spins down (free tier)
5. **First request after spin-down**: Backend takes 10-15 seconds to start

**Result**: Your FINALTrip website is live on the internet! 🎉

---

## 📞 Quick Reference

**If deployment fails**, check these in order:

1. **Git Push** - Did you push all changes?
   ```bash
   git status  # Should show "nothing to commit"
   ```

2. **Procfile** - Does it exist and have exactly this?
   ```
   web: gunicorn api:app
   ```

3. **requirements.txt** - Does it have gunicorn?
   ```bash
   grep gunicorn requirements.txt
   ```

4. **Environment Variables** - Configured in both Vercel and Render?
   - Vercel: `VITE_API_URL`
   - Render: `FLASK_ENV`, `CORS_ORIGINS`

5. **Database** - Is production.db in your repo?
   ```bash
   ls -lh production.db  # Should be ~15 MB
   ```

If all 5 are ✅, your deployment should work!

---

## 🎓 Learning Resources

- **Vercel Docs**: https://vercel.com/docs
- **Render Docs**: https://render.com/docs
- **Flask & Gunicorn**: https://gunicorn.org/
- **Vite React**: https://vitejs.dev/

---

**Last Updated**: January 26, 2026  
**Your Deployment URL**: Will be assigned during setup  
**Expected Status**: LIVE in 30 minutes! 🚀
