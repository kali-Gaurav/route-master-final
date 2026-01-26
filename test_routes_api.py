#!/usr/bin/env python3
"""
Test Server for Optimized Routes API

Minimal Flask app to test the optimized routes API endpoints.
"""

from flask import Flask
from optimized_routes_api import init_optimized_routes_api
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Register optimized routes API
init_optimized_routes_api(app)

# Root endpoint
@app.route('/')
def index():
    return {
        'message': 'Optimized Route Generator API',
        'version': '1.0',
        'endpoints': {
            'GET /api/routes/optimized': 'Find routes with transfers',
            'GET /api/routes/direct': 'Find direct routes only',
            'GET /api/routes/alternatives': 'Find all route alternatives',
            'GET /api/routes/health': 'Check API status',
            'GET /api/routes/stats': 'Get graph statistics'
        },
        'example': '/api/routes/optimized?start=Adavali&end=Vaibhavwadi%20Rd&transfers=3'
    }


if __name__ == '__main__':
    print("\n" + "="*70)
    print("OPTIMIZED ROUTES API TEST SERVER")
    print("="*70)
    print("\nStarting Flask server...")
    print("Visit: http://localhost:5000")
    print("\nExample endpoints:")
    print("  http://localhost:5000/api/routes/optimized?start=Adavali&end=Vaibhavwadi%20Rd")
    print("  http://localhost:5000/api/routes/health")
    print("  http://localhost:5000/api/routes/stats")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
