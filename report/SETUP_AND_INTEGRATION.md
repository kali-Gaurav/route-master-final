# Route Master - IRCTC Live Train Route Optimizer

A full-stack application that generates Pareto-optimal train routes using the IRCTC RapidAPI with real-time validation for seat availability, fares, and live locations.

## Features

- **Pareto-Optimal Route Generation**: Finds non-dominated routes across multiple objectives (time, cost, transfers)
- **IRCTC API Integration**: Real-time validation using IRCTC RapidAPI
- **Top 10 Route Validation**: Automatically validates the top 10 optimal routes with:
  - Live seat availability
  - Current fares
  - Live train locations
- **Multi-Transfer Support**: Supports 0-3 transfers for maximum flexibility
- **Interactive Frontend**: React + Vite UI for searching and comparing routes

## Prerequisites

- Python 3.8+
- Node.js 16+ / npm or Bun
- IRCTC RapidAPI Key (already configured)

## Installation

### 1. Backend Setup

```powershell
# Navigate to project directory
cd "c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\route-master-final"

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```powershell
# In the same directory
npm install
# or if using Bun:
# bun install
```

## Running the Application

### Start Backend (Port 5000)

```powershell
python api.py
```

Output will show:
```
 * Running on http://127.0.0.1:5000
```

### Start Frontend (Port 5173)

```powershell
npm run dev
# or with Bun:
# bun run dev
```

Output will show:
```
VITE v5.4.19  ready in 200 ms

➜  Local:   http://localhost:5173/
```

Then open: **http://localhost:5173/**

## API Endpoints

### Get Optimal Routes (with IRCTC Validation)
```
GET /api/routes?origin=PGT&destination=KOTA&max_transfers=3&date=25-01-2026
```
**Response**: Top 10 routes validated with IRCTC API, including:
- Seat availability
- Real-time fares
- Live locations
- Validation metadata

### Get Live Station Data
```
GET /api/live-station?station=PGT&hours=1
```

### Get Seat Availability
```
GET /api/seat-availability?train=12345&source=PGT&destination=KOTA&date=25-01-2026
```

### Get Train Fare
```
GET /api/fare?train=12345&source=PGT&destination=KOTA&date=25-01-2026
```

### Validate Multiple Routes
```
POST /api/validate-routes
Content-Type: application/json

{
  "routes": [...],
  "date": "25-01-2026"
}
```

## IRCTC API Configuration

The application uses the following IRCTC RapidAPI endpoints:
- `getLiveStation`: Get live trains at a station
- `getSeatAvailability`: Check seat availability for a train
- `getFare`: Get current fare for a train
- `getLiveLocation`: Get real-time train location

API Key is configured in [api.py](api.py#L18).

## Architecture

```
route-master-final/
├── api.py                          # Flask backend with IRCTC integration
├── route_optimizer.py              # Pareto optimization engine
├── Train_details.csv               # Train dataset
├── package.json                    # Frontend dependencies (React/Vite)
├── src/                            # React component source
├── requirements.txt                # Python dependencies
└── [route data files]              # Cached routes (JSON/CSV)
```

## How It Works

1. **Route Generation**: Generates all feasible routes (200-300) using multi-strategy search
2. **Pareto Optimization**: Filters to non-dominated routes using multi-objective optimization
3. **Top 10 Selection**: Picks 7 diverse optimal routes + top 3 backups
4. **IRCTC Validation**: Validates each of top 10 routes with:
   - Real-time seat availability
   - Current fares
   - Live locations
5. **Results**: Returns validated routes with pricing and availability data

## Example Usage

```python
# Python example
import requests

# Get routes from PGT to KOTA
response = requests.get(
    'http://localhost:5000/api/routes',
    params={
        'origin': 'PGT',
        'destination': 'KOTA',
        'max_transfers': 3,
        'date': '25-01-2026'
    }
)

routes = response.json()
print(f"Found {len(routes['optimal_routes'])} optimal routes")

# Check validation status
for route in routes['optimal_routes']:
    validation = route.get('irctc_validation', {})
    print(f"Route valid: {validation.get('valid')}")
```

## Troubleshooting

### Backend won't start
- Check Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Ensure port 5000 is available

### Frontend won't start
- Check Node is installed: `node --version`
- Install packages: `npm install`
- Clear node_modules if needed: `rm -r node_modules && npm install`

### IRCTC API Errors
- Verify API key is valid in [api.py](api.py#L18)
- Check internet connection
- IRCTC API may have rate limits - wait a moment and retry

### Train data not found
- Ensure `Train_details.csv` exists in project root
- File should have 186,000+ train records

## Performance Notes

- **Route generation**: 5-30 seconds depending on source/destination connectivity
- **IRCTC validation**: ~2-5 seconds per route (top 10 = 20-50 seconds total)
- **Caching**: Results cached in memory for faster subsequent requests
- **Database**: Uses in-memory graph for O(E log V) Dijkstra complexity

## Future Enhancements

- [ ] User authentication and booking integration
- [ ] Push notifications for price drops
- [ ] Historical data analysis
- [ ] Advanced filtering (coach class, train type, etc.)
- [ ] Mobile app version

## License

Proprietary - IIT Palakkad Startup Project

## Support

For API issues, check IRCTC RapidAPI documentation at https://rapidapi.com/API-MATIC/api/irctc1
