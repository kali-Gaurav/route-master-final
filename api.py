from flask import Flask, request, jsonify
from flask_cors import CORS
from route_optimizer import get_routes_data
import os

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/api/routes', methods=['GET'])
def get_routes():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    max_transfers = request.args.get('max_transfers', type=int, default=3)
    travel_date_str = request.args.get('travel_date') # Get travel_date as string

    if not origin or not destination:
        return jsonify({"error": "Origin and destination are required."}), 400

    # Call the core logic function
    results, router = get_routes_data(origin.upper(), destination.upper(), max_transfers, travel_date_str)

    if results and "error" in results:
        return jsonify(results), 400
    
    # The router object itself is not JSON serializable, so we don't return it
    # get_routes_data already saves the JSON data to a file,
    # but we can return the 'results' dictionary which contains the JSON content
    return jsonify(results), 200

if __name__ == '__main__':
    # You can set the port here, 5000 is common for Flask APIs
    app.run(debug=True, port=5000)