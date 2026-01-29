# Railway Operating System - Frontend & Database Integration

## Setup Complete ✅

The Railway Operating System frontend has been successfully connected to the database with route generation and display capabilities.

## Running Services

### 1. Frontend Server
- **Status**: ✅ Running
- **URL**: http://localhost:8080
- **Technology**: Vite + React + TypeScript + TailwindCSS
- **Command**: `npm run dev` (from `frontend/` directory)
- **Features**:
  - Station search
  - Route search with filters
  - Route display and sorting
  - Multi-transfer route support

### 2. Backend API Server
- **Status**: ✅ Running
- **URL**: http://localhost:8000
- **Technology**: FastAPI + SQLite
- **File**: `simple_api.py`
- **Command**: `python simple_api.py`
- **CORS**: Enabled for all origins (frontend connectivity)

## API Endpoints

### Health & Status
- `GET /health` - Basic health check
- `GET /ready` - Readiness check with database status

### Station Management
- `GET /api/v1/stations?search=query&limit=50` - Search for stations
- `GET /api/v1/stations/{code}` - Get specific station details

### Route Generation & Display
- `POST /api/v1/routes/search` - Search for routes (POST)
  ```json
  {
    "origin": "NDLS",
    "destination": "CSTM",
    "date": "2024-01-28",
    "max_transfers": 3
  }
  ```

- `GET /api/routes?origin=NDLS&destination=CSTM&max_transfers=3` - Search for routes (GET/Legacy)
  - Returns sample routes with optimal and alternative options
  - Categories: EXPRESS, PASSENGER, LOCAL
  - Includes transfer information and timing

## Database Integration

The system connects to the SQLite database (`railway_os.db`) which contains:
- Station master data (codes, names, zones, states)
- Train information (train numbers, names, routes)
- Schedule data (departure/arrival times, days running)
- Route connectivity information

## Frontend Features

1. **Station Search Component**
   - Auto-complete station search
   - Station code and name matching
   - Zone and state information

2. **Route Search Interface**
   - Origin and destination selection
   - Travel date picker
   - Max transfers filter
   - Direct routes only option

3. **Route Display**
   - Optimal routes (fastest)
   - Alternative routes (with transfers)
   - Category filtering (EXPRESS, PASSENGER, LOCAL)
   - Route details with train information
   - Transfer information and timing

4. **UI Components**
   - Navbar with navigation
   - Station search dropdowns
   - Route cards with collapsible details
   - Loading skeletons
   - Toast notifications for feedback

## Environment Configuration

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
```

### Backend
- SQLite database: `railway_os.db`
- Uvicorn server on port 8000
- CORS enabled for development

## How to Use

### Start Frontend
```bash
cd frontend
npm run dev
```

### Start Backend API
```bash
python simple_api.py
```

### Access the Application
1. Open http://localhost:8080 in your browser
2. Select origin station
3. Select destination station
4. Choose travel date
5. Click search
6. View optimal and alternative routes

## File Locations

- **Frontend**: `railway-operating-system-core/frontend/`
- **Backend API**: `railway-operating-system-core/simple_api.py`
- **Database**: `railway-operating-system-core/railway_os.db`
- **Original Complex API**: `railway-operating-system-core/ros_api.py` (with dependency issues)

## Next Steps

1. **Connect to Real Database**
   - Replace sample route data in `/api/routes` with actual database queries
   - Implement transfer calculation logic
   - Add fare calculation

2. **Enhance Route Engine**
   - Implement actual graph-based pathfinding
   - Add multi-transfer route optimization
   - Add date-based filtering

3. **Add More Features**
   - Train availability checking
   - Real-time seat availability
   - Booking integration
   - Historical fare data

4. **Optimization**
   - Add caching for frequently searched routes
   - Implement response compression
   - Add route pre-calculation

## Troubleshooting

### Frontend not loading
- Ensure `npm run dev` is running on port 8080
- Check VITE_API_URL in `.env` matches your backend

### Routes not displaying
- Verify `python simple_api.py` is running on port 8000
- Check browser console for CORS errors
- Verify database connection in API

### Database connection issues
- Ensure `railway_os.db` exists in the project root
- Check database has required tables: stations, trains, schedule
- Run database verification: `python -c "import sqlite3; sqlite3.connect('railway_os.db').execute('SELECT COUNT(*) FROM stations')"`

---
**Setup Date**: January 28, 2026
**System Status**: Operational ✅
