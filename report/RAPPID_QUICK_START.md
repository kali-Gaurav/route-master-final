# 🚀 RAPPID Integration - Quick Start Guide

## 5-Minute Setup

### Step 1: Install (No new dependencies needed!)
All required packages already installed in your project.

### Step 2: Start Backend
```bash
python api.py
```

Output:
```
===========================
ROUTE MASTER - INTEGRATED BACKEND (RAPPID + IRCTC)
Flask API Server with Live Train Route Optimization & Real-time Validation
===========================

🚀 Starting backend server on http://127.0.0.1:5000

📚 API ENDPOINTS:
   ROUTE OPTIMIZATION:
   - GET /api/routes (main endpoint - returns optimized routes with validation)

   RAPPID API INTEGRATION:
   - GET /api/train-data
   - GET /api/train-schedule
   - GET /api/train-seats
   - GET /api/train-fares
   - GET /api/train-status
   - POST /api/validate-route-rappid
   - POST /api/validate-routes-rappid

   DUAL VALIDATION (RAPPID + IRCTC):
   - POST /api/validate-routes-dual
   
✨ Features:
   ✓ Real-time train schedule validation
   ✓ Live seat availability checking
   ✓ Dynamic fare calculation
   ✓ Train status & delay monitoring
   ✓ Coach composition analysis
   ✓ Dual API validation (RAPPID + IRCTC)
```

### Step 3: Test Endpoints

#### Get Train Data
```bash
curl "http://localhost:5000/api/train-data?train_no=16320"
```

#### Search Routes with Validation
```bash
# RAPPID validation only
curl "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=rappid"

# Dual validation (RAPPID + IRCTC) - RECOMMENDED
curl "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=dual"
```

#### Validate a Route
```bash
curl -X POST "http://localhost:5000/api/validate-route-rappid" \
  -H "Content-Type: application/json" \
  -d '{
    "route": {
      "source": "ADI",
      "destination": "HWH",
      "segments": [{"train_no": "16320", "from": "ADI", "to": "HWH"}]
    },
    "date": "26-01-2026"
  }'
```

---

## 🎯 Common Use Cases

### Use Case 1: Get Seat Availability
```bash
curl "http://localhost:5000/api/train-seats?train_no=16320"

# Response:
{
  "train_no": "16320",
  "seat_info": {
    "available": 45,
    "classes": {
      "SL": 20,
      "3A": 15,
      "2A": 10
    }
  }
}
```

### Use Case 2: Check Current Fares
```bash
curl "http://localhost:5000/api/train-fares?train_no=16320"

# Shows: Base fare, total fare, per-class pricing
```

### Use Case 3: Get Train Status
```bash
curl "http://localhost:5000/api/train-status?train_no=16320"

# Shows: On-time status, delays, platform info
```

### Use Case 4: Search & Validate Routes
```bash
curl "http://localhost:5000/api/routes?origin=ADI&destination=HWH&validation=dual&date=26-01-2026"

# Returns: Top 10 routes with RAPPID + IRCTC validation
# Each route includes: seats, fares, train status, coaches, etc.
```

---

## 📊 Response Structure

### All responses include:
```json
{
  "data": {
    // Real-time information from RAPPID
  },
  "timestamp": "2026-01-24T10:30:00.000Z",
  "source": "RAPPID API"
}
```

### Validated routes include:
```json
{
  "rappid_validation": {
    "valid": true,
    "segments": [...],
    "summary": {
      "total_fare": 500,
      "total_available_seats": 45,
      "all_trains_on_time": true,
      "average_validation_score": 92.5
    }
  }
}
```

---

## 🔧 Configuration

### Timeout (default: 10 seconds)
In `api.py`:
```python
rappid_client = RAPPIDAPIClient(timeout=15)  # Change as needed
```

### Retry Attempts (default: 3)
```python
rappid_client = RAPPIDAPIClient(retry_attempts=5)
```

### Cache Duration (default: 5 minutes)
In `rappid_integration.py`:
```python
CACHE_DURATION = 600  # 10 minutes
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No response | Check if backend is running: `http://localhost:5000/api/health` |
| Invalid train | Use valid train number (e.g., 16320) |
| Slow response | First call is slower (API fetch), cached calls are instant |
| Outdated data | Cache expires in 5 minutes, will auto-refresh |

---

## ✅ Health Check

```bash
curl "http://localhost:5000/api/health"

# Response:
{
  "status": "healthy",
  "timestamp": "2026-01-24T10:30:00.000Z",
  "irctc_api_configured": true,
  "rappid_api_configured": true,
  "dual_validation_available": true
}
```

---

## 📚 Full Documentation

See [RAPPID_INTEGRATION_GUIDE.md](RAPPID_INTEGRATION_GUIDE.md) for complete documentation.

---

## 🎓 Testing Train Numbers

Use these valid Indian train numbers for testing:

- **16320** - Common express train
- **12302** - Rajdhani Express
- **15708** - Regional express
- **20940** - Humsafar Express

---

## 💡 Tips

1. **First call is slower** - API fetch takes 1-2 seconds
2. **Cached calls are instant** - Within 5 minutes, <100ms response
3. **Use dual validation** - More accurate results (parameter: `?validation=dual`)
4. **Check logs** - Run with logging to see what's happening
5. **Monitor health** - Periodically check `/api/health`

---

## 🚀 Next Steps

1. Test individual endpoints
2. Integrate with frontend
3. Monitor response times
4. Enable detailed logging if needed
5. Scale based on usage

---

**Questions?** Check the full [RAPPID_INTEGRATION_GUIDE.md](RAPPID_INTEGRATION_GUIDE.md)

**Version:** 1.0  
**Status:** ✅ Ready to Use
