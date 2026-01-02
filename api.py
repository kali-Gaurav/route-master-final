from flask import Flask, request, jsonify
from flask_cors import CORS
from route_optimizer import get_routes_data
import os
import json

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Simple in-memory cache
cache = {}

@app.route('/api/routes', methods=['GET'])
def get_routes():
    origin = request.args.get('origin', '').upper()
    destination = request.args.get('destination', '').upper()
    # Enforce a maximum of 3 transfers as requested
    max_transfers = min(request.args.get('max_transfers', type=int, default=3), 3)

    if not origin or not destination:
        return jsonify({"error": "Origin and destination are required."}), 400

    cache_key = f"{origin}_{destination}_{max_transfers}"
    
    if cache_key in cache:
        return jsonify(cache[cache_key]), 200

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