#!/usr/bin/env python3
"""
Route Generation API Integration

Flask blueprint for serving optimized routes via REST API.
Integrates the OptimizedRouteGenerator with the main Flask app.

Endpoints:
- GET /api/routes/optimized?start=...&end=...&transfers=3
- GET /api/routes/direct?start=...&end=...
- GET /api/routes/alternatives?start=...&end=...
"""

from flask import Blueprint, request, jsonify
from optimized_route_generator import OptimizedRouteGenerator
import logging
from functools import lru_cache
import time

logger = logging.getLogger(__name__)

# Initialize generator globally (loaded once)
_generator = None
_generator_ready = False

def get_generator():
    """Lazy-load the route generator (build graph on first request)."""
    global _generator, _generator_ready
    
    if _generator is None:
        _generator = OptimizedRouteGenerator()
    
    if not _generator_ready:
        logger.info("Initializing optimized route generator...")
        stats = _generator.build_graph()
        _generator_ready = True
        logger.info(f"Graph ready: {stats}")
    
    return _generator


# Create Blueprint
routes_bp = Blueprint('optimized_routes', __name__, url_prefix='/api/routes')


@routes_bp.route('/optimized', methods=['GET'])
def get_optimized_routes():
    """
    Get optimized routes with up to 3 transfers.
    
    Query Parameters:
    - start: Starting station name (required)
    - end: Destination station name (required)
    - transfers: Max transfers allowed (optional, default 3)
    
    Returns:
    - routes grouped by number of transfers
    - search time and statistics
    """
    try:
        start = request.args.get('start', '').strip()
        end = request.args.get('end', '').strip()
        transfers = int(request.args.get('transfers', 3))
        
        # Validation
        if not start or not end:
            return jsonify({
                'error': 'Missing parameters',
                'required': ['start', 'end'],
                'optional': ['transfers']
            }), 400
        
        if transfers < 0 or transfers > 5:
            return jsonify({'error': 'Transfers must be between 0 and 5'}), 400
        
        # Get generator and find routes
        generator = get_generator()
        result = generator.find_routes(start, end, max_transfers=transfers)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in get_optimized_routes: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/direct', methods=['GET'])
def get_direct_routes():
    """
    Get only direct routes (no transfers).
    
    Query Parameters:
    - start: Starting station (required)
    - end: Destination station (required)
    
    Returns:
    - List of direct routes
    """
    try:
        start = request.args.get('start', '').strip()
        end = request.args.get('end', '').strip()
        
        if not start or not end:
            return jsonify({'error': 'start and end parameters required'}), 400
        
        generator = get_generator()
        routes = generator.find_direct_routes(start, end)
        
        return jsonify({
            'start': start,
            'end': end,
            'direct_routes': routes,
            'count': len(routes)
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_direct_routes: {e}")
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/alternatives', methods=['GET'])
def get_route_alternatives():
    """
    Get comprehensive route alternatives (direct + multi-transfer).
    
    Query Parameters:
    - start: Starting station (required)
    - end: Destination station (required)
    - transfers: Max transfers (optional, default 3)
    
    Returns:
    - Direct routes
    - Multi-transfer routes grouped by transfers
    - Total routes and search metrics
    """
    try:
        start = request.args.get('start', '').strip()
        end = request.args.get('end', '').strip()
        transfers = int(request.args.get('transfers', 3))
        
        if not start or not end:
            return jsonify({'error': 'start and end parameters required'}), 400
        
        generator = get_generator()
        result = generator.get_route_details(start, end, max_transfers=transfers)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error in get_route_alternatives: {e}")
        return jsonify({'error': str(e)}), 500


@routes_bp.route('/health', methods=['GET'])
def health_check():
    """
    Check if route generator is ready.
    
    Returns:
    - Graph status and statistics
    """
    try:
        generator = get_generator()
        
        return jsonify({
            'status': 'ready' if generator.graph_built else 'building',
            'graph_built': generator.graph_built,
            'stations': len(generator.stations),
            'edges': sum(len(edges) for edges in generator.graph.values()),
            'build_time_ms': round(generator.build_time * 1000, 2),
            'timestamp': time.time()
        }), 200
    
    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500


@routes_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get detailed graph and performance statistics.
    
    Returns:
    - Graph metrics
    - Performance characteristics
    - Algorithm details
    """
    try:
        generator = get_generator()
        
        if not generator.graph_built:
            return jsonify({'error': 'Graph not built yet'}), 503
        
        # Calculate some statistics
        total_edges = sum(len(edges) for edges in generator.graph.values())
        max_edges = max((len(edges) for edges in generator.graph.values()), default=0)
        min_edges = min((len(edges) for edges in generator.graph.values()), default=0)
        
        return jsonify({
            'graph_status': 'ready',
            'total_stations': len(generator.stations),
            'total_edges': total_edges,
            'avg_degree': round(total_edges / len(generator.stations), 2) if generator.stations else 0,
            'max_degree': max_edges,
            'min_degree': min_edges,
            'build_time_ms': round(generator.build_time * 1000, 2),
            'algorithm': {
                'name': 'Breadth-First Search (BFS)',
                'max_transfers': 3,
                'time_complexity': 'O(V + E)',
                'space_complexity': 'O(V)',
                'typical_search_time_ms': '<100ms'
            },
            'database': {
                'path': generator.db_path,
                'type': 'SQLite'
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500


# Integration function for main app
def init_optimized_routes_api(app):
    """
    Register the optimized routes blueprint with the main Flask app.
    
    Usage in main API file:
    ```python
    from optimized_routes_api import init_optimized_routes_api
    init_optimized_routes_api(app)
    ```
    """
    app.register_blueprint(routes_bp)
    logger.info("Optimized routes API initialized")
