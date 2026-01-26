# Solution: Search Failed Error

## Quick Diagnosis

When you see "Search Failed", it means the frontend can't get a response from the backend API.

### Step 1: Check if the API is Running

Open a new terminal and run:
```bash
python quick_api_test.py
```

**If you see "[ERROR] Cannot connect to localhost:5000":**
→ **The API is not running!** See "Starting the API" below.

**If you see "[OK] Found N optimal routes":**
→ **The API is working!** See "Debugging the Frontend" below.

---

## Fix 1: Starting the API

### If API is not running:

**Option A: Quick Start Batch File** (Easiest)
```bash
START_SERVERS.bat
```

**Option B: Manual - PowerShell**
```powershell
cd "C:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final"
python api.py
```

**Option C: Manual - Command Prompt**
```cmd
cd C:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final
python api.py
```

**Wait for this message:**
```
 * Running on http://127.0.0.1:5000
```

### Common API Startup Issues

**"ModuleNotFoundError: No module named..."**
- Fix: `pip install -r requirements.txt`

**"Address already in use"**
- Another process is using port 5000
- Find and close the other process, or:
- Edit api.py, change `5000` to another port (e.g., `5001`)

---

## Fix 2: Starting the Frontend

If API is running but you still get "Search Failed":

### Open a NEW terminal window and run:

**PowerShell:**
```powershell
npm run dev
```

**Command Prompt:**
```cmd
npm run dev
```

**Wait for:**
```
Local: http://localhost:5173/
```

### Common Frontend Issues

**"npm: command not found"**
- Install Node.js: https://nodejs.org/
- Then: `npm install` in project folder

**"Port 5173 is in use"**
- Vite will use next port (5174, 5175, etc)
- Check the terminal output for the actual URL

---

## Fix 3: Debugging the Search

Once both servers are running:

### In the browser (http://localhost:5173):

1. **Open Developer Tools** (F12 or Ctrl+Shift+I)
2. **Go to "Console" tab**
3. **Try the search again**
4. **Look for messages starting with `[Search]`**

#### You should see:
```
[Search] Calling API: http://localhost:5000/api/routes?origin=NDLS&destination=KOTA
[Search] Response status: 200 Time: 45000 ms
[Search] Response data: { optimal_routes: [...], ... }
```

#### If you see an error:
```
[ERROR] Cannot connect to server at localhost:5000. Make sure 'python api.py' is running.
```
→ Go back to **Fix 1: Starting the API**

```
[ERROR] API returned error: Station 'NDLS' not found.
```
→ The stations don't exist in the dataset
→ Try: NDLS, KOTA, PGT, HWH, CSMT

---

## Fix 4: Network Tab Debug

If console shows no messages:

1. **Open DevTools** (F12)
2. **Go to "Network" tab**
3. **Try search**
4. **Look for request to `/api/routes`**

#### Check:
- **URL:** Should be `http://localhost:5000/api/routes?origin=...`
- **Status:** Should be `200` (not red)
- **Response:** Should show JSON with `optimal_routes`

#### If request is red (failed):
- Check API is running: `python quick_api_test.py`
- Check no errors in API terminal window
- Check firewall isn't blocking localhost

---

## Fix 5: Reset Everything

If all else fails:

**Step 1:** Close all terminal windows (both API and frontend)

**Step 2:** In your project folder:
```bash
# Clear cache
rm -r .next* dist
npm cache clean --force
pip cache purge
```

**Step 3:** Reinstall dependencies:
```bash
npm install
pip install --upgrade -r requirements.txt
```

**Step 4:** Start fresh:
```bash
python api.py
# In another terminal:
npm run dev
```

---

## Reference: Test Commands

Use these to verify each component:

```bash
# Test if API server is running
python quick_api_test.py

# Test if data loads correctly
python debug_search.py

# Full system diagnostic
python DIAGNOSTIC.py

# Test API directly (requires API to be running)
curl "http://localhost:5000/api/health"
```

---

## Still Not Working?

Please run these and share the output:

```bash
python DIAGNOSTIC.py
python debug_search.py
python quick_api_test.py
```

And check these files for errors:
- `api_errors.log`
- `api_startup.log`
- Browser console (F12)
