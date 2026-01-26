# Search Failed - Troubleshooting Guide

## Issue
When you enter origin and destination stations and press search, you get "Search Failed" error.

## Root Cause Analysis Checklist

### 1. Verify Both Servers Are Running

**Frontend (Port 5173):**
```bash
npm run dev
```
Check that it shows:
```
  VITE v... ready in ... ms

  ➜  Local:   http://localhost:5173/
```

**Backend (Port 5000):**
```bash
python api.py
```
Check that it shows:
```
 * Running on http://127.0.0.1:5000
```

### 2. Check Browser Console for Errors

1. Open your browser's Developer Tools (F12 or Ctrl+Shift+I)
2. Go to the "Console" tab
3. Try the search again
4. Look for any error messages

### 3. Check Network Tab

1. Open Developer Tools
2. Go to "Network" tab
3. Try the search
4. Look for the request to `localhost:5000/api/routes`
5. Check:
   - Status code (should be 200, not 500, 404, etc.)
   - Response body (should have `optimal_routes` array)
   - If it shows CORS error, there's a connection issue

## Solution Steps

### Option 1: Run Both Servers (Recommended)

**Terminal 1 - Start Backend:**
```bash
cd C:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final
python api.py
```

Wait for the message: `* Running on http://127.0.0.1:5000`

**Terminal 2 - Start Frontend:**
```bash
cd C:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final
npm run dev
```

Wait for: `Local: http://localhost:5173/`

### Option 2: Test API Directly

Run the test script to verify the API is working:
```bash
python test_api_direct.py
```

If this shows "[ERROR] Connection error", your Flask API is not running.

## Quick Debug

### If You See "Connection Error"
- Make sure `python api.py` is running in another terminal
- Check that Python is in your PATH
- Try: `pip install -r requirements.txt` to ensure all dependencies are installed

### If You See "Station Not Found"
- The station codes from the frontend must match exactly the station codes in `Train_details.csv`
- They should be uppercase (the API converts them automatically)
- Run: `python debug_search.py` to verify stations are being loaded

### If You See "No Routes Found"
- There might be no valid train routes between those stations on that date
- Try other station pairs like:
  - NDLS -> KOTA
  - PGT -> KOTA  
  - HWH -> CSMT

## Common Issues & Fixes

### Issue: "npm: command not found"
**Fix:** Install Node.js from https://nodejs.org/
Then: `npm install` in the project folder

### Issue: "ModuleNotFoundError" when running api.py
**Fix:** Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Port 5000 already in use
**Fix:** Change the port in api.py or kill the process using port 5000

### Issue: Port 5173 already in use
**Fix:** Vite will use the next available port (5174, 5175, etc.)

## Verification Checklist

- [ ] `python api.py` is running and shows "Running on http://127.0.0.1:5000"
- [ ] `npm run dev` is running and shows "Local: http://localhost:5173/"
- [ ] Browser console has no CORS errors
- [ ] Network tab shows 200 status for API requests
- [ ] Selected stations (NDLS, KOTA, etc.) appear in the station search dropdown

## Contact Information

If issues persist:
1. Run `python debug_search.py` and share the output
2. Run `python test_api_direct.py` and share the output
3. Check the `api_errors.log` file for backend errors
