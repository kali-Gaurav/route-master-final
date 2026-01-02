# Route Master Upgrade

This project has been upgraded with the following features:

1.  **Dynamic Route Optimization**: The web app now calls a Flask backend to calculate real-time Pareto-optimal routes based on your selected origin and destination.
2.  **Comprehensive Station Search**: Over 8,000 stations are now indexed and mapped to cities. You can search by station code, station name, or city name.
3.  **Optimal vs. All Routes**: You can now toggle between viewing the "Optimal" (Pareto-front) routes and "All Possible" routes found by the algorithm.
4.  **Backend Caching**: Repeated searches are now cached in the backend for near-instant results.

## How to Run

### 1. Start the Backend API
Make sure you have the virtual environment active and dependencies installed.
```bash
# Install dependencies if not already done
pip install flask flask-cors pandas numpy

# Run the API
python api.py
```
The API will run on `http://localhost:5000`.

### 2. Start the Frontend
In a separate terminal:
```bash
bun dev
# or
npm run dev
```
The web app will be available at the URL provided by Vite (usually `http://localhost:5173`).

## Data Generation
If you need to regenerate the station-city mapping:
```bash
python generate_station_city_mapping.py
```
This will update `src/data/station_search_data.json`.
