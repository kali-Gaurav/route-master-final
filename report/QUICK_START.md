# 🚀 Route Master - Quick Start Guide

## What's Been Done

✅ **IRCTC RapidAPI Integration Complete**
- API key configured: `e0adaea886msh3fb9b9456cad9ccp17a317jsna7fe7b2fe0b6`
- All endpoints integrated for real-time validation
- Top 10 routes automatically validated with:
  - Live seat availability
  - Current fares
  - Train status & locations

## 5-Minute Setup

### Step 1: Open Terminal/PowerShell
Navigate to the project folder:
```powershell
cd "c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final"
```

### Step 2: Install Dependencies (First Time Only)
```powershell
pip install -r requirements.txt
npm install
```

### Step 3: Start Backend (Port 5000)
```powershell
python api.py
```
You should see:
```
✓ Flask API Server running on http://127.0.0.1:5000
```

### Step 4: Open Another Terminal & Start Frontend (Port 5173)
```powershell
npm run dev
```
You should see:
```
VITE v5.4.19 ready in X ms
Local: http://localhost:5173/
```

### Step 5: Open in Browser
Click or visit: **http://localhost:5173/**

---

## Using the Application

### 1. Search for Routes
- Enter **Origin** (e.g., `PGT`)
- Enter **Destination** (e.g., `KOTA`)
- Optionally set **Travel Date** (defaults to tomorrow)
- Click **Search**

### 2. View Results
The system will:
1. Generate 200-300 possible routes (5-30 sec)
2. Optimize using Pareto algorithm
3. Validate top 10 with IRCTC API (20-50 sec)

### 3. Check Validated Data
Each route shows:
- ⚡ Time to destination
- 💰 Total fare (from IRCTC)
- 🔄 Number of transfers
- 🪑 Available seats (from IRCTC)
- ✅ Validation status

---

## API Endpoints (For Developers)

### Main Route Search (with IRCTC validation)
```bash
curl "http://localhost:5000/api/routes?origin=PGT&destination=KOTA&max_transfers=3&date=25-01-2026"
```

### Check Live Station Status
```bash
curl "http://localhost:5000/api/live-station?station=PGT&hours=1"
```

### Check Seat Availability
```bash
curl "http://localhost:5000/api/seat-availability?train=12345&source=PGT&destination=KOTA&date=25-01-2026"
```

### Check Fares
```bash
curl "http://localhost:5000/api/fare?train=12345&source=PGT&destination=KOTA&date=25-01-2026"
```

### Health Check
```bash
curl "http://localhost:5000/api/health"
```

---

## Automated Startup (Windows)

**Option 1: Batch File**
```powershell
.\start.bat
```
This opens both backend and frontend in separate windows automatically.

**Option 2: Manual Both**
```powershell
# Terminal 1
python api.py

# Terminal 2
npm run dev
```

---

## Testing the Integration

Run the complete test suite:
```powershell
python test_irctc_integration.py
```

This tests:
- ✓ Live station data
- ✓ Seat availability
- ✓ Fare information
- ✓ Full route optimization
- ✓ IRCTC validation

---

## Documentation

📖 **Detailed Guides**:
- [Full Setup & Integration](SETUP_AND_INTEGRATION.md)
- [IRCTC API Details](IRCTC_INTEGRATION_DETAILS.md)
- [Architecture & Data Flow](pareto_optimizer_docs.md)

---

## Troubleshooting

### "Port 5000 already in use"
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or use different port in api.py
app.run(port=5001)
```

### "No module named 'flask'"
```powershell
pip install -r requirements.txt
```

### "npm: command not found"
Install Node.js from https://nodejs.org/

### IRCTC API errors
- Verify API key is set in [api.py](api.py#L17)
- Check internet connection
- Check RapidAPI dashboard for quota/status

---

## Key Features

🚀 **Route Optimization**
- Pareto-optimal algorithm finds best routes across 5 objectives
- Time, cost, transfers, comfort, safety

🌐 **Live Data**
- Real-time seat availability from IRCTC
- Current fares updated dynamically
- Train status & locations

💾 **Intelligent Caching**
- In-memory caching for repeated searches
- Disk-based routes for faster loading
- Reduces IRCTC API calls

📊 **Comprehensive Results**
- Up to 10 optimized routes per search
- All segments validated with IRCTC
- Detailed comparison table

---

## Next Steps

### For Users
1. Search for routes
2. Compare fares and times
3. Book through IRCTC (upcoming feature)

### For Developers
1. Study the codebase in [route_optimizer.py](route_optimizer.py)
2. Review IRCTC integration in [api.py](api.py#L15-L95)
3. Extend with custom features

### Production Deployment
1. Move API key to environment variables
2. Set up proper logging
3. Add database for persistence
4. Deploy backend (Heroku, AWS, GCP)
5. Deploy frontend (Netlify, Vercel)

---

## Support

- 📧 Email: support@routemaster.local
- 🐛 Issues: Check documentation first
- 🔑 API Help: https://rapidapi.com/API-MATIC/api/irctc1

---

**Happy Route Planning! 🚆**
