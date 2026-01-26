# Summary of Search Failed Issue & Fixes

## Problem
When you enter origin and destination and press search, you get "Search Failed" error message.

## Root Cause
The frontend cannot connect to the backend API, either because:
1. The API server (`python api.py`) is not running
2. The frontend server (`npm run dev`) is not running  
3. There's a network/port issue
4. There's an error in the API that prevents it from responding

## What I Fixed

### 1. Enhanced Frontend Error Messages
**File:** `src/pages/Index.tsx`

Added detailed console logging to help identify the issue:
- Logs the API URL being called
- Logs the response status and time
- Logs any errors with details
- Shows better error messages in the toast notification

**How to use:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Try the search
4. Look for messages starting with `[Search]`
5. This will show you exactly what went wrong

### 2. Created Multiple Diagnostic Scripts

**quick_api_test.py:**
- Tests if the API server is running
- Tests if it can process a route request
- Shows any error responses

**debug_search.py:**
- Tests if the data loads correctly
- Tests if the graph is built properly
- Tests if the router initializes correctly

**DIAGNOSTIC.py:**
- Complete system check
- Verifies all files exist
- Checks port availability
- Tests API connection

**Usage:**
```bash
python quick_api_test.py    # Test API server
python debug_search.py      # Test data loading
python DIAGNOSTIC.py        # Full system check
```

### 3. Created Startup Helper

**START_SERVERS.bat:**
- Double-click to automatically start both frontend and backend
- Installs dependencies if needed
- Opens both servers in separate windows

**Usage:**
```bash
START_SERVERS.bat
```

### 4. Created Comprehensive Troubleshooting Guide

**FIX_SEARCH_FAILED.md:**
- Step-by-step diagnosis process
- Solutions for common issues
- Network debugging instructions
- Reset/recovery procedures

## How to Use the Fix

### Step 1: Run Diagnostics
```bash
python DIAGNOSTIC.py
```

This will tell you which parts are working and which aren't.

### Step 2: Start Both Servers

Option A - Automatic:
```bash
START_SERVERS.bat
```

Option B - Manual:
```bash
# Terminal 1
python api.py

# Terminal 2 (new window)
npm run dev
```

Wait for both servers to say they're running:
- API: ` * Running on http://127.0.0.1:5000`
- Frontend: `Local: http://localhost:5173/`

### Step 3: Test in Browser

1. Open http://localhost:5173
2. Select origin: NDLS
3. Select destination: KOTA
4. Click Search
5. Open DevTools (F12 → Console tab)
6. Look for the `[Search]` messages

### Step 4: If Still Failing

Check the messages in the console:
- If `[ERROR] Cannot connect to server`: API is not running → Fix 1
- If `[ERROR] API Error: ...`: Check API window for error messages
- If no messages appear: Check browser is loading the latest code (Ctrl+Shift+R)

## Key Files Modified

1. **src/pages/Index.tsx** - Added detailed error logging
2. **Created:** quick_api_test.py - API test script
3. **Created:** debug_search.py - Data loading test
4. **Created:** DIAGNOSTIC.py - System diagnostic
5. **Created:** START_SERVERS.bat - Automated startup
6. **Created:** FIX_SEARCH_FAILED.md - Troubleshooting guide

## Testing Checklist

- [ ] Both servers are running (check terminal windows)
- [ ] Frontend shows: Local: http://localhost:5173/
- [ ] Backend shows: Running on http://127.0.0.1:5000
- [ ] Can open browser to http://localhost:5173
- [ ] Can select stations in the search box
- [ ] Browser console shows [Search] messages
- [ ] Search completes (may take 30-60 seconds first time)
- [ ] Routes are displayed

## If You Still Have Issues

1. Run: `python DIAGNOSTIC.py`
2. Check the error messages in browser Console (F12)
3. Check the error messages in the API terminal window
4. Read: FIX_SEARCH_FAILED.md for specific solutions
5. Try a different station pair (not all routes may exist)

## Performance Notes

- First search for a route pair: 30-60 seconds (generates and optimizes routes)
- Cached searches: < 1 second
- Network request time is shown in console: `Time: XXX ms`
- Large time values (30000+ ms) mean the API is still calculating
