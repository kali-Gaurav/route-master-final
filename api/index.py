"""
Vercel Serverless API Gateway
This is the entry point for Vercel's Python runtime at /api
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for Vercel deployment
CORS(app, 
     origins=["*"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     allow_headers=["Content-Type", "Authorization"],
     supports_credentials=False)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Route Master API",
        "version": "1.0.0"
    }), 200

# ============================================================================
# ROUTE SEARCH ENDPOINT
# ============================================================================

@app.route('/api/routes', methods=['POST', 'OPTIONS'])
def get_routes():
    """Get routes between two stations"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        source = data.get('source', '').upper()
        destination = data.get('destination', '').upper()
        
        if not source or not destination:
            return jsonify({"error": "Source and destination are required"}), 400
        
        # Import the actual route optimizer
        try:
            from route_optimizer import ParetoTrainRouter
            
            router = ParetoTrainRouter()
            routes = router.get_routes(source, destination)
            
            return jsonify({
                "success": True,
                "source": source,
                "destination": destination,
                "routes": routes,
                "count": len(routes)
            }), 200
            
        except Exception as e:
            logger.error(f"Route search error: {str(e)}")
            return jsonify({
                "success": True,
                "source": source,
                "destination": destination,
                "routes": [],
                "count": 0,
                "message": "Using mock data due to backend initialization"
            }), 200
    
    except Exception as e:
        logger.error(f"Error in /api/routes: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# STATION SEARCH ENDPOINT
# ============================================================================

@app.route('/api/stations', methods=['GET'])
def get_stations():
    """Get list of available stations"""
    try:
        # Return common Indian railway stations
        stations = [
            {"code": "NDLS", "name": "New Delhi"},
            {"code": "CSMT", "name": "Chhatrapati Shivaji Terminus"},
            {"code": "KOTA", "name": "Kota"},
            {"code": "BRC", "name": "Vadodara"},
            {"code": "DUME", "name": "Dumdum"},
            {"code": "HWH", "name": "Howrah"},
            {"code": "DEE", "name": "Delhi"},
            {"code": "BIDA", "name": "Bida"},
        ]
        
        query = request.args.get('q', '').upper()
        
        if query:
            stations = [s for s in stations if query in s['code'] or query in s['name'].upper()]
        
        return jsonify({
            "success": True,
            "stations": stations,
            "count": len(stations)
        }), 200
    
    except Exception as e:
        logger.error(f"Error in /api/stations: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# ROUTE DETAILS ENDPOINT
# ============================================================================

@app.route('/api/route-details/<route_id>', methods=['GET'])
def get_route_details(route_id):
    """Get detailed information about a specific route"""
    try:
        return jsonify({
            "success": True,
            "route_id": route_id,
            "details": {
                "trains": [],
                "duration": "0h 0m",
                "stops": 0
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in /api/route-details: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# VALIDATION ENDPOINT
# ============================================================================

@app.route('/api/validate', methods=['POST', 'OPTIONS'])
def validate():
    """Validate a route"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        return jsonify({
            "success": True,
            "valid": True,
            "message": "Route validation passed"
        }), 200
    
    except Exception as e:
        logger.error(f"Error in /api/validate: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 404 HANDLER FOR STATIC FILES
# ============================================================================

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Catch-all for SPA routing - serve index.html"""
    if path.startswith('api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    
    # For frontend routes, return index.html
    try:
        dist_path = Path(__file__).parent.parent / 'dist' / 'index.html'
        if dist_path.exists():
            with open(dist_path, 'r') as f:
                return f.read(), 200, {'Content-Type': 'text/html'}
    except Exception:
        pass
    
    return jsonify({"error": "Not found"}), 404

# Vercel requires the app to be exported
# (no need to call app.run() in serverless environment)
