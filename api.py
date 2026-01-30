from flask import Flask, request, jsonify
from flask_cors import CORS
from route_optimizer import get_routes_data
import os
import json

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Simple in-memory cache
cache = {}

def load_cached_routes(origin, destination):
    """
    Check if pre-computed route files exist for the given origin-destination pair.
    Returns the loaded JSON data if files exist, None otherwise.
    """
    json_file = f"{origin}_to_{destination}_pareto_routes.json"
    csv_file = f"{origin}_to_{destination}_pareto_routes.csv"
    
    # Check if both files exist
    if os.path.exists(json_file) and os.path.exists(csv_file):
        try:
            print(f"📂 Loading cached routes from {json_file}")
            with open(json_file, 'r') as f:
                cached_data = json.load(f)
            print(f"✓ Successfully loaded {len(cached_data.get('optimal_routes', []))} cached routes")
            return cached_data
        except Exception as e:
            print(f"⚠️ Error loading cached file: {e}")
            return None
    
    return None

@app.route('/api/routes', methods=['GET'])
def get_routes():
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    # Enforce a maximum of 3 transfers as requested
    max_transfers = min(request.args.get('max_transfers', type=int, default=3), 3)

    if not origin or not destination:
        return jsonify({"error": "Origin and destination are required."}), 400

    cache_key = f"{origin}_{destination}_{max_transfers}"
    
    # Check in-memory cache first
    if cache_key in cache:
        print(f"💾 Returning routes from memory cache for {origin} → {destination}")
        return jsonify(cache[cache_key]), 200

    # Check for pre-computed files on disk
    cached_routes = load_cached_routes(origin, destination)
    if cached_routes:
        # Store in memory cache for future requests
        cache[cache_key] = cached_routes
        return jsonify(cached_routes), 200

    # If no cached files found, proceed with route calculation
    print(f"🔄 No cached files found. Computing routes for {origin} → {destination}...")
    
    # Call the core logic function
    results, router = get_routes_data(origin, destination, max_transfers)

    if results and "error" in results:
        return jsonify(results), 400
    
    # Store in cache
    cache[cache_key] = results
    
    return jsonify(results), 200

if __name__ == '__main__':
    # You can set the port here, 5000 is common for Flask APIs
    app.run(debug=False, port=5000)