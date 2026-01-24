from flask import Flask, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from typing import Optional # Add this import
import asyncio
import aiohttp # For async HTTP requests
import pandas as pd
from route_optimizer import get_routes_data, ParetoTrainRouter
from rappid_integration import RAPPIDAPIClient, RAPPIDRouteValidator
from rappid_optimized import OptimizedRAPPIDClient, CacheWarmer
from real_time_api_wrapper import ApiLiveFetcher
from irctc_client import (
    IRCTC_API_KEY, IRCTC_API_HOST, IRCTC_BASE_URL, get_irctc_headers,
    get_live_station_data, get_seat_availability, get_train_fare,
    validate_route_with_irctc
)
from optimization_engine import (
    OptimizedGraphBuilder, OptimizedParetoOptimizer, OptimizedSerializer,
    graph_builder, pareto_optimizer, serializer, perf_monitor
)
import os
import sys
import requests # Still needed for rappid_optimized, which is not yet async
import json
import pickle
from datetime import datetime, timedelta
import logging
import re
import csv
from pathlib import Path
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("route_master_api")
logger.setLevel(logging.INFO)

app = Flask("route-master-api", static_url_path='', static_folder='.')
CORS(app)
app.start_time = time.time()

# Global variables
GLOBAL_TRAIN_DF = None
GLOBAL_GRAPH = defaultdict(list)
STATION_MAPS = {
    'station_to_id': {},
    'id_to_station': {}
}
aiohttp_session: Optional[aiohttp.ClientSession] = None # Global aiohttp session
executor = ThreadPoolExecutor(max_workers=4)
_event_loop: Optional[asyncio.AbstractEventLoop] = None
_loop_lock = threading.Lock()

def get_event_loop():
    """Get or create an event loop for the thread"""
    global _event_loop
    try:
        loop = asyncio.get_running_loop()
        return loop
    except RuntimeError:
        pass
    
    with _loop_lock:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

# Decorator to wrap async route handlers for Flask
def async_route(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Get the current Flask request context BEFORE entering the thread
        from flask import copy_current_request_context
        
        async def run_async():
            global aiohttp_session
            # Ensure aiohttp session is created
            if aiohttp_session is None:
                aiohttp_session = aiohttp.ClientSession()
            try:
                return await f(*args, **kwargs)
            finally:
                # Keep session open for reuse
                pass
        
        # Run async function in a new thread with its own event loop
        @copy_current_request_context
        def run_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(run_async())
            finally:
                loop.close()
        
        # Execute in thread pool
        future = executor.submit(run_in_thread)
        return future.result()
    
    return wrapper

_before_serving = getattr(app, "before_serving", None)
_after_serving = getattr(app, "after_serving", None)


async def _ensure_aiohttp_session() -> aiohttp.ClientSession:
    """Lazy initialization of aiohttp ClientSession - only creates when first needed"""
    global aiohttp_session
    # Check if session exists and is still open
    if aiohttp_session is None:
        logger.info("Creating aiohttp ClientSession...")
        aiohttp_session = aiohttp.ClientSession()
    elif aiohttp_session.closed:
        logger.info("Recreating closed aiohttp ClientSession...")
        aiohttp_session = aiohttp.ClientSession()
    return aiohttp_session

def _load_global_train_data():
    """Loads Train_details.csv once globally at application startup."""
    global GLOBAL_TRAIN_DF
    try:
        logger.info("Loading Train_details.csv globally...")
        df = pd.read_csv('Train_details.csv', low_memory=False)
        GLOBAL_TRAIN_DF = df[df['Train No'].astype(str).str.len() == 5].copy()
        logger.info(f"Successfully loaded {len(GLOBAL_TRAIN_DF)} train details globally.")
    except FileNotFoundError:
        logger.critical("Train_details.csv not found. Please ensure the file is in the root directory.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Error loading Train_details.csv: {e}", exc_info=True)
        sys.exit(1)

def _calculate_static_duration(departure_str, arrival_str):
    """Helper to calculate duration in hours."""
    try:
        fmt = '%H:%M:%S'
        t1 = datetime.strptime(departure_str, fmt)
        t2 = datetime.strptime(arrival_str, fmt)
        if t2 < t1:
            t2 += timedelta(days=1)
        return (t2 - t1).total_seconds() / 3600
    except (ValueError, TypeError):
        return 0

def _build_global_graph():
    """
    Builds the master graph from GLOBAL_TRAIN_DF at startup using optimized builder.
    This is now O(E) instead of O(E^2) thanks to itertuples and batch processing.
    """
    global GLOBAL_GRAPH, STATION_MAPS, GLOBAL_TRAIN_DF
    
    logger.info("Building optimized global static train graph...")
    start_time = time.time()
    
    if GLOBAL_TRAIN_DF is None:
        logger.error("GLOBAL_TRAIN_DF is not loaded. Cannot build graph.")
        return

    # Use the optimized graph builder
    graph_data = graph_builder.build_from_dataframe(GLOBAL_TRAIN_DF)
    
    GLOBAL_GRAPH = graph_data['adjacency_list']
    STATION_MAPS['station_to_id'] = graph_data['station_to_id']
    STATION_MAPS['id_to_station'] = graph_data['id_to_station']
    
    elapsed = time.time() - start_time
    station_count = len(STATION_MAPS.get('station_to_id', {}))
    edge_count = sum(len(v) for v in GLOBAL_GRAPH.values())
    
    logger.info(f"Optimized graph built in {elapsed:.2f}s")
    logger.info(f"  Stations: {station_count}, Edges: {edge_count}")

# Load data when the application starts
_load_global_train_data()
_build_global_graph()

# Initialize optimized RAPPID API Client (still synchronous for now)
rappid_client = OptimizedRAPPIDClient(timeout=10, retry_attempts=3)
rappid_validator = RAPPIDRouteValidator(rappid_client)


# Async setup for Flask app
if _before_serving:
    @_before_serving
    async def startup_event():
        await _ensure_aiohttp_session()

if _after_serving:
    @_after_serving
    async def shutdown_event():
        global aiohttp_session
        if aiohttp_session:
            logger.info("Closing aiohttp ClientSession...")
            await aiohttp_session.close()
            aiohttp_session = None

# Simple in-memory cache for routes (replace with LRUCache from cachetools as per roadmap)
cache = {}


def _parse_travel_date(value: str) -> datetime:
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.now()


def _clamp_max_transfers(value: str | int | None) -> int:
    try:
        transfers = int(value)
    except (TypeError, ValueError):
        transfers = 3
    return max(0, min(3, transfers))


def _normalize_validation_mode(value: str) -> str:
    normalized = (value or "dual").lower()
    return normalized if normalized in {"dual", "rappid", "irctc"} else "dual"

def load_cached_routes(origin, destination, journey_date: datetime):
    """
    Check if pre-computed route files exist for the given origin-destination pair and journey date.
    Returns the loaded JSON data if files exist, None otherwise.
    """
    date_str = journey_date.strftime('%Y%m%d')
    pickle_file = f"{origin}_to_{destination}_pareto_routes_{date_str}.pkl"
    
    if os.path.exists(pickle_file):
        try:
            logger.info(f"📂 Loading cached routes from {pickle_file}")
            with open(pickle_file, 'rb') as f:
                cached_data = pickle.load(f)
            logger.info(f"✓ Successfully loaded {len(cached_data.get('optimal_routes', []))} cached routes from disk.")
            return cached_data
        except Exception as e:
            logger.warning(f"⚠️ Error loading cached file {pickle_file}: {e}")
            return None
    
    return None

# Root route - serve index.html
@app.route('/', methods=['GET'])
def root():
    """Serve the index.html file for the frontend"""
    try:
        return app.send_static_file('index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return jsonify({
            "message": "Welcome to Route Master API",
            "documentation": "See API endpoints at /api/routes and other /api/* endpoints",
            "health_check": "/api/health"
        }), 200

# Fallback route for serving index.html for client-side routing
@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    """Serve static files and fallback to index.html for client-side routing"""
    if path and ('.' in path):  # Has extension - try to serve as file
        try:
            return app.send_static_file(path)
        except Exception:
            pass  # File not found, continue
    
    # Fallback to index.html for client-side routing
    try:
        return app.send_static_file('index.html')
    except Exception as e:
        logger.error(f"Error serving static file {path}: {e}")
        return jsonify({"error": f"Not found: {path}"}), 404

@app.route('/api/routes', methods=['GET'])
@async_route
async def routes_endpoint():
    global aiohttp_session
    try:
        logger.info(f"[ROUTES] Starting route request: origin={request.args.get('origin')}, dest={request.args.get('destination')}")
        
        origin = request.args.get('origin', '').strip().upper()
        destination = request.args.get('destination', '').strip().upper()
        if not origin or not destination:
            return jsonify({"error": "Origin and destination are required."}), 400

        max_transfers = _clamp_max_transfers(request.args.get('max_transfers', 3))
        validation_mode = _normalize_validation_mode(request.args.get('validation', 'dual'))
        travel_date_raw = request.args.get('date', datetime.now().strftime('%d-%m-%Y'))
        travel_date_obj = _parse_travel_date(travel_date_raw)
        travel_date_str = travel_date_obj.strftime('%d-%m-%Y')
        logger.info(f"[ROUTES] Parsed params: origin={origin}, dest={destination}, transfers={max_transfers}, date={travel_date_str}")

        validate_irctc = validation_mode in ('irctc', 'dual')
        validate_rappid = validation_mode in ('rappid', 'dual')
        validation_sources = []
        if validate_irctc:
            validation_sources.append('IRCTC API')
        if validate_rappid:
            validation_sources.append('RAPPID API')

        cache_key = f"{origin}_{destination}_{max_transfers}_{travel_date_obj.strftime('%Y%m%d')}_{validation_mode}"
        
        # Ensure aiohttp_session is initialized
        logger.info("[ROUTES] Ensuring aiohttp session...")
        aiohttp_session = await _ensure_aiohttp_session()
        
        # Create the ApiLiveFetcher instance, passing the aiohttp session
        logger.info("[ROUTES] Creating ApiLiveFetcher...")
        api_fetcher = ApiLiveFetcher(
            rappid_client=rappid_client,
            aiohttp_session=aiohttp_session
        )

        # Check in-memory cache first
        if cache_key in cache:
            logger.info(f"[ROUTES] Cache hit for {origin} -> {destination}")
            return jsonify(cache[cache_key]), 200

        # Check for pre-computed files on disk
        logger.info("[ROUTES] Checking disk cache...")
        cached_routes_from_disk = load_cached_routes(origin, destination, travel_date_obj)
        if cached_routes_from_disk:
            logger.info(f"[ROUTES] Re-validating {len(cached_routes_from_disk.get('all_generated_routes', []))} disk-cached routes for {origin} to {destination} on {travel_date_str}...")
        
            revalidated_optimal_routes = []
            revalidated_all_routes = []

            # Helper to re-validate and filter routes
            async def revalidate_and_filter_routes(routes_list, api_fetcher_instance, j_date, global_df):
                revalidated_list = []
                # Need a dummy router instance to call calculate_route_objectives for re-validation
                # This uses the globally loaded DataFrame
                dummy_router_for_revalidation = ParetoTrainRouter(GLOBAL_GRAPH, STATION_MAPS, api_fetcher_instance, j_date, global_df)
                
                # Collect all segment re-validation tasks
                segment_revalidation_tasks = []
                for route_data in routes_list:
                    for segment in route_data['segments']:
                        segment_revalidation_tasks.append(
                            api_fetcher_instance.fetch_segment_data(
                                train_no=segment['train_no'],
                                from_station_code=segment['from'],
                                to_station_code=segment['to'],
                                journey_date=j_date,
                                travel_class='SL' # Default to Sleeper
                            )
                        )
                
                all_live_data_results = await asyncio.gather(*segment_revalidation_tasks)
                
                # Now distribute results back and re-validate routes
                result_idx = 0
                for route_data in routes_list:
                    current_route_segments = route_data['segments']
                    is_route_available = True
                    updated_segments = []
                    
                    for segment in current_route_segments:
                        live_data = all_live_data_results[result_idx]
                        result_idx += 1
                        
                        segment['live_seat_availability'] = live_data['availability']
                        segment['live_fare'] = live_data['fare']

                        if not live_data['availability'].startswith("AVAILABLE"):
                            is_route_available = False
                            break # This segment is unavailable, so the whole route is unavailable
                        updated_segments.append(segment)
                    
                    if is_route_available:
                        # Recalculate objectives for the re-validated route using the dummy router
                        updated_route_objectives = dummy_router_for_revalidation.calculate_route_objectives(updated_segments)
                        updated_route_data = route_data.copy()
                        updated_route_data['segments'] = updated_segments
                        updated_route_data['objectives'] = updated_route_objectives
                        revalidated_list.append(updated_route_data)
                    else:
                        logger.debug(f"Route {route_data.get('route_id', '')} filtered out due to unavailable segment.")

                return revalidated_list

            revalidated_all_routes = await revalidate_and_filter_routes(
                cached_routes_from_disk.get('all_generated_routes', []), api_fetcher, travel_date_obj, GLOBAL_TRAIN_DF
            )
            revalidated_optimal_routes = await revalidate_and_filter_routes(
                cached_routes_from_disk.get('optimal_routes', []), api_fetcher, travel_date_obj, GLOBAL_TRAIN_DF
            )

            revalidated_results = {
                'metadata': cached_routes_from_disk.get('metadata', {}),
                'optimal_routes': revalidated_optimal_routes,
                'all_generated_routes': revalidated_all_routes
            }

            if 'optimal_routes' in revalidated_results:
                revalidated_results['validation_metadata'] = {
                    'validated_at': datetime.now().isoformat(),
                    'travel_date': travel_date_str,
                    'routes_validated': len(revalidated_optimal_routes),
                    'validation_source': validation_mode.upper(),
                    'apis_used': ['IRCTC'], # Only IRCTC used for re-validation here
                    'from_cache': True,
                    'revalidated': True
                }
            
            # Store re-validated data in memory cache
            cache[cache_key] = revalidated_results
            return jsonify(revalidated_results), 200

        # If no cached files found, proceed with route calculation
        logger.info(f"[ROUTES] No cached files found. Computing routes for {origin} to {destination} on {travel_date_str}...")
        
        # Call the core logic function with global df, api_fetcher and journey_date
        results, router = await get_routes_data(
            origin, destination, max_transfers, GLOBAL_GRAPH, STATION_MAPS, api_fetcher, travel_date_obj, GLOBAL_TRAIN_DF
        )

        if results and "error" in results:
            return jsonify(results), 400
        
        # Cache and return results
        logger.info(f"[ROUTES] Route calculation complete. Caching results...")
        cache[cache_key] = results
        
        return jsonify(results), 200

    except Exception as e:
        logger.error(f"[ROUTES] ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[ROUTES] Traceback:\n{error_trace}")
        return jsonify({
            "error": f"Internal server error: {type(e).__name__}: {str(e)}",
            "trace": str(error_trace) if app.debug else None
        }), 500

@app.route('/api/live-station', methods=['GET'])
@async_route
async def live_station_endpoint():
    """Get live station data from IRCTC API"""
    station_code = request.args.get('station', '').upper()
    hours = request.args.get('hours', type=int, default=1)
    
    if not station_code:
        return jsonify({"error": "Station code is required."}) , 400
    
    data = await get_live_station_data(aiohttp_session, station_code, hours) # AWAIT and pass session
    if data:
        return jsonify(data.model_dump()), 200 # Return model_dump
    else:
        return jsonify({"error": "Failed to fetch live station data from IRCTC"}), 500

@app.route('/api/seat-availability', methods=['GET'])
@async_route
async def seat_availability_endpoint():
    """Get seat availability from IRCTC API"""
    train_no = request.args.get('train', '')
    source = request.args.get('source', '').upper()
    destination = request.args.get('destination', '').upper()
    date = request.args.get('date', datetime.now().strftime('%d-%m-%Y'))
    
    if not train_no or not source or not destination:
        return jsonify({"error": "Train number, source, and destination are required."}) , 400
    
    data = await get_seat_availability(aiohttp_session, train_no, source, destination, date) # AWAIT and pass session
    if data:
        return jsonify(data.model_dump()), 200 # Return model_dump
    else:
        return jsonify({"error": "Failed to fetch seat availability from IRCTC"}), 500

@app.route('/api/fare', methods=['GET'])
@async_route
async def fare_endpoint():
    """Get train fare from IRCTC API"""
    train_no = request.args.get('train', '')
    source = request.args.get('source', '').upper()
    destination = request.args.get('destination', '').upper()
    date = request.args.get('date', datetime.now().strftime('%d-%m-%Y'))
    
    if not train_no or not source or not destination:
        return jsonify({"error": "Train number, source, and destination are required."}) , 400
    
    data = await get_train_fare(aiohttp_session, train_no, source, destination, date) # AWAIT and pass session
    if data:
        return jsonify(data.model_dump()), 200 # Return model_dump
    else:
        return jsonify({"error": "Failed to fetch fare from IRCTC"}), 500

@app.route('/api/validate-routes', methods=['POST'])
@async_route
async def validate_routes_endpoint():
    """
    Validate multiple routes using IRCTC API
    Expects: {routes: [...], date: 'DD-MM-YYYY'}
    """
    data = request.get_json()
    
    if not data or 'routes' not in data:
        return jsonify({"error": "Routes data is required."}) , 400
    
    travel_date = data.get('date', datetime.now().strftime('%d-%m-%Y'))
    routes = data.get('routes', [])
    
    validated_routes = []
    for route in routes[:10]:  # Validate top 10
        validated_route = await validate_route_with_irctc(aiohttp_session, route, travel_date) # AWAIT HERE
        validated_routes.append(validated_route)
    
    return jsonify({
        'validated_routes': validated_routes,
        'total_validated': len(validated_routes),
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/train-data', methods=['GET'])
def get_train_data_endpoint():
    """
    Get comprehensive train data from RAPPID API
    Query params: train_no (required)
    Returns: All available data for the train
    """
    train_no = request.args.get('train_no', '').strip()
    
    if not train_no:
        return jsonify({"error": "train_no parameter is required."}) , 400
    
    logger.info(f"Fetching RAPPID data for train {train_no}")
    
    data = rappid_client.get_train_data(train_no, use_cache=True)
    
    if not data:
        return jsonify({
            "error": f"Could not fetch data for train {train_no}",
            "train_no": train_no
        }), 500
    
    return jsonify({
        'train_no': train_no,
        'data': data,
        'timestamp': datetime.now().isoformat(),
        'source': 'RAPPID API'
    }), 200


@app.route('/api/train-schedule', methods=['GET'])
def get_train_schedule_endpoint():
    """
    Get train schedule details from RAPPID API
    Query params: train_no (required)
    """
    try:
        train_no = request.args.get('train_no', '').strip()
        
        if not train_no:
            return jsonify({"error": "train_no parameter is required."}) , 400
        
        schedule = rappid_client.get_train_schedule(train_no)
        
        if not schedule:
            return jsonify({
                "error": f"Could not fetch schedule for train {train_no}",
                "train_no": train_no
            }), 404
        
        return jsonify(schedule), 200
    except Exception as e:
        logger.error(f"Error in train-schedule endpoint: {e}", exc_info=True)
        return jsonify({
            "error": f"Error fetching schedule: {str(e)}",
            "train_no": train_no if 'train_no' in locals() else 'unknown'
        }), 500


@app.route('/api/train-seats', methods=['GET'])
def get_train_seats_endpoint():
    """
    Get seat availability from RAPPID API
    Query params: train_no (required)
    """
    try:
        train_no = request.args.get('train_no', '').strip()
        
        if not train_no:
            return jsonify({"error": "train_no parameter is required."}) , 400
        
        seats = rappid_client.get_seat_availability(train_no)
        
        if not seats:
            return jsonify({
                "error": f"Could not fetch seat availability for train {train_no}",
                "train_no": train_no
            }), 404
        
        return jsonify(seats), 200
    except Exception as e:
        logger.error(f"Error in train-seats endpoint: {e}", exc_info=True)
        return jsonify({
            "error": f"Error fetching seats: {str(e)}",
            "train_no": train_no if 'train_no' in locals() else 'unknown'
        }), 500


@app.route('/api/train-fares', methods=['GET'])
def get_train_fares_endpoint():
    """
    Get fare information from RAPPID API
    Query params: train_no (required)
    """
    try:
        train_no = request.args.get('train_no', '').strip()
        
        if not train_no:
            return jsonify({"error": "train_no parameter is required."}) , 400
        
        fares = rappid_client.get_fare_information(train_no)
        
        if not fares:
            return jsonify({
                "error": f"Could not fetch fares for train {train_no}",
                "train_no": train_no
            }), 404
        
        return jsonify(fares), 200
    except Exception as e:
        logger.error(f"Error in train-fares endpoint: {e}", exc_info=True)
        return jsonify({
            "error": f"Error fetching fares: {str(e)}",
            "train_no": train_no if 'train_no' in locals() else 'unknown'
        }), 500


@app.route('/api/train-status', methods=['GET'])
def get_train_status_endpoint():
    """
    Get current train status and delays from RAPPID API
    Query params: train_no (required)
    """
    try:
        train_no = request.args.get('train_no', '').strip()
        
        if not train_no:
            return jsonify({"error": "train_no parameter is required."}) , 400
        
        status = rappid_client.get_train_status(train_no)
        
        if not status:
            return jsonify({
                "error": f"Could not fetch status for train {train_no}",
                "train_no": train_no
            }), 404
        
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error in train-status endpoint: {e}", exc_info=True)
        return jsonify({
            "error": f"Error fetching status: {str(e)}",
            "train_no": train_no if 'train_no' in locals() else 'unknown'
        }), 500


@app.route('/api/validate-route-rappid', methods=['POST'])
def validate_route_rappid_endpoint():
    """
    Validate a single route using RAPPID API
    Body: {route: {...}, date: 'DD-MM-YYYY' (optional)}
    """
    data = request.get_json()
    
    if not data or 'route' not in data:
        return jsonify({"error": "Routes data is required."}) , 400
    
    route = data.get('route')
    travel_date = data.get('date', datetime.now().strftime('%d-%m-%Y'))
    
    logger.info(f"Validating route using RAPPID API")
    
    validated_route = rappid_validator.validate_route(route, travel_date)
    
    return jsonify(validated_route), 200


@app.route('/api/validate-routes-rappid', methods=['POST'])
def validate_routes_rappid_endpoint():
    """
    Validate multiple routes using RAPPID API
    Body: {routes: [...], date: 'DD-MM-YYYY' (optional)}
    """
    data = request.get_json()
    
    if not data or 'routes' not in data:
        return jsonify({"error": "Routes data is required."}) , 400
    
    routes = data.get('routes', [])
    travel_date = data.get('date', datetime.now().strftime('%d-%m-%Y'))
    
    logger.info(f"Validating {len(routes)} routes using RAPPID API")
    
    result = rappid_validator.validate_routes_batch(routes, travel_date)
    
    return jsonify(result), 200


@app.route('/api/seat-availability-by-train', methods=['GET'])
async def seat_availability_by_train():
    """Convenience endpoint: given `train_no` returns seat availability.

    If `source` and `destination` are not provided, returns the RAPPID route
    (station list) so the caller can choose stations for availability checks.
    """
    train_no = request.args.get('train_no', '').strip()
    source = request.args.get('source', '').upper().strip()
    destination = request.args.get('destination', '').upper().strip()
    date = request.args.get('date', datetime.now().strftime('%d-%m-%Y'))

    if not train_no:
        return jsonify({"error": "train_no parameter is required."}) , 400

    try:
        # Get RAPPID schedule/route to help the user pick stations
        schedule = rappid_client.get_train_schedule(train_no)
        route = schedule.get('route', []) if schedule else []

        # If user did not supply source/destination, return route to help pick
        if not source or not destination:
            return jsonify({
                "train_no": train_no,
                "note": "Provide `source` and `destination` (station codes) to check seat availability. Use `route` below to pick stations.",
                "route": route,
                "route_count": len(route)
            }), 200

        # If source/destination provided, call IRCTC seat availability helper
        seat_data = await get_seat_availability(aiohttp_session, train_no, source, destination, date) # AWAIT HERE
        if seat_data:
            return jsonify(seat_data.model_dump()), 200 # Return model_dump
        else:
            return jsonify({"error": "Failed to fetch seat availability from IRCTC"}), 500

    except Exception as e:
        logger.error(f"Error in seat-availability-by-train endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e), "train_no": train_no}), 500


@app.route('/api/validate-routes-dual', methods=['POST'])
@async_route
async def validate_routes_dual_endpoint():
    """
    Validate routes using BOTH RAPPID and IRCTC APIs for comprehensive validation
    Body: {routes: [...], date: 'DD-MM-YYYY' (optional)}
    Returns: Routes with both RAPPID and IRCTC validation data
    """
    data = request.get_json()
    
    if not data or 'routes' not in data:
        return jsonify({"error": "Routes data is required."}) , 400
    
    travel_date = data.get('date', datetime.now().strftime('%d-%m-%Y'))
    routes = data.get('routes', [])
    
    logger.info(f"🔄 Dual validation of {len(routes)} routes (RAPPID + IRCTC)")
    
    validated_routes = []
    
    for idx, route in enumerate(routes[:10], 1):  # Validate top 10
        logger.info(f"  Processing route {idx}/10")
        
        # Validate with RAPPID (still synchronous)
        rappid_validated = rappid_validator.validate_route(route, travel_date)
        
        # Validate with IRCTC
        irctc_validated = await validate_route_with_irctc(aiohttp_session, route, travel_date) # AWAIT HERE and pass session
        
        # Merge both validations
        merged_route = rappid_validated.copy()
        merged_route['irctc_validation'] = irctc_validated.get('irctc_validation', {})
        
        # Create comprehensive validation summary
        merged_route['validation_summary'] = {
            'rappid_valid': rappid_validated.get('rappid_validation', {}).get('valid', False),
            'irctc_valid': irctc_validated.get('irctc_validation', {}).get('valid', False),
            'overall_valid': (
                rappid_validated.get('rappid_validation', {}).get('valid', False) and
                irctc_validated.get('irctc_validation', {}).get('valid', False)
            ),
            'rappid_score': rappid_validated.get('rappid_validation', {}).get('summary', {}).get('average_validation_score', 0),
            'validation_timestamp': datetime.now().isoformat()
        }
        
        validated_routes.append(merged_route)
    
    return jsonify({
        'validated_routes': validated_routes,
        'total_routes': len(validated_routes),
        'valid_routes': sum(1 for r in validated_routes if r.get('validation_summary', {}).get('overall_valid')),
        'validation_sources': ['RAPPID API', 'IRCTC API'],
        'travel_date': travel_date,
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    rappid_dir = Path('data/rappid')
    rappid_count = len(list(rappid_dir.glob('*.json'))) if rappid_dir.exists() else 0
    last_refresh = None
    if rappid_count > 0:
        latest_file = max(rappid_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, default=None)
        if latest_file:
            last_refresh = datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'irctc_api_configured': True,
        'rappid_api_configured': True,
        'dual_validation_available': True,
        'rappid_json_count': rappid_count,
        'rappid_last_refresh': last_refresh
    }), 200


@app.route('/api/rappid-data/<train_no>', methods=['GET'])
def get_rappid_data(train_no: str):
    """Serve stored RAPPID JSON for a specific train."""
    try:
        train_no = train_no.strip()
        if not train_no or not re.match(r'^\d+$', train_no):
            return jsonify({"error": "Invalid train_no format"}), 400
        
        json_path = Path('data/rappid') / f"{train_no}.json"
        if not json_path.exists():
            return jsonify({"error": f"No stored RAPPID data for train {train_no}"}), 404
        
        with json_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"Error serving RAPPID data: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/admin/refresh-rappid/<train_no>', methods=['POST'])
def refresh_rappid_single(train_no: str):
    """Refresh RAPPID data for a single train."""
    try:
        train_no = train_no.strip()
        if not train_no or not re.match(r'^\d+$', train_no):
            return jsonify({"error": "Invalid train_no format"}), 400
        
        # Fetch from RAPPID
        data = rappid_client.get_train_data(train_no, use_cache=False)
        if not data:
            return jsonify({
                "train_no": train_no,
                "status": "error",
                "message": "Failed to fetch from RAPPID API"
            }), 500
        
        # Save to data/rappid/
        json_dir = Path('data/rappid')
        json_dir.mkdir(parents=True, exist_ok=True)
        json_path = json_dir / f"{train_no}.json"
        
        with_meta = {
            "fetched_at": datetime.utcnow().isoformat(),
            "train_no": train_no,
            "response": data
        }
        with json_path.open('w', encoding='utf-8') as f:
            json.dump(with_meta, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "train_no": train_no,
            "status": "success",
            "message": f"Refreshed RAPPID data for train {train_no}",
            "saved_to": str(json_path),
            "fetched_at": with_meta["fetched_at"]
        }), 200
    except Exception as e:
        logger.error(f"Error refreshing RAPPID for {train_no}: {e}", exc_info=True)
        return jsonify({"error": str(e), "train_no": train_no}), 500


@app.route('/admin/refresh-rappid-bulk', methods=['POST'])
def refresh_rappid_bulk():
    """Bulk refresh RAPPID data for multiple trains."""
    try:
        payload = request.get_json() or {}
        train_nos = payload.get('train_numbers', [])
        
        if not isinstance(train_nos, list) or not train_nos:
            return jsonify({"error": "Provide 'train_numbers' as a list"}), 400
        
        # Validate format
        train_nos = [str(t).strip() for t in train_nos if str(t).strip()]
        invalid = [t for t in train_nos if not re.match(r'^\d+$', t)]
        if invalid:
            return jsonify({"error": f"Invalid train numbers: {invalid}"}), 400
        
        json_dir = Path('data/rappid')
        json_dir.mkdir(parents=True, exist_ok=True)
        
        results = {"success": [], "failed": []}
        for train_no in train_nos:
            try:
                data = rappid_client.get_train_data(train_no, use_cache=False)
                if not data:
                    results["failed"].append({"train_no": train_no, "reason": "API returned None"})
                    continue
                
                json_path = json_dir / f"{train_no}.json"
                with_meta = {
                    "fetched_at": datetime.utcnow().isoformat(),
                    "train_no": train_no,
                    "response": data
                }
                with json_path.open('w', encoding='utf-8') as f:
                    json.dump(with_meta, f, ensure_ascii=False, indent=2)
                
                results["success"].append({"train_no": train_no, "saved_to": str(json_path)})
            except Exception as e:
                results["failed"].append({"train_no": train_no, "reason": str(e)})
        
        return jsonify({
            "total_requested": len(train_nos),
            "successful": len(results["success"]),
            "failed": len(results["failed"]),
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"Error in bulk refresh: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/admin/status/rappid', methods=['GET'])
def rappid_status():
    """Get RAPPID data status: file counts, refresh times, missing trains."""
    try:
        json_dir = Path('data/rappid')
        json_files = list(json_dir.glob('*.json')) if json_dir.exists() else []
        
        # Count stored files
        file_count = len(json_files)
        
        # Find last refresh
        last_refresh = None
        if json_files:
            latest = max(json_files, key=lambda p: p.stat().st_mtime, default=None)
            last_refresh = datetime.fromtimestamp(latest.stat().st_mtime).isoformat()
    
        # Extract train numbers from stored files
        stored_trains = {f.stem for f in json_dir.glob('*.json')} # Corrected: json_files was not defined
        
        # Find trains from all CSVs
        all_trains = set()
        for csv_file in Path('.').glob('*_all_routes.csv'):
            with csv_file.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                possible_keys = [k for k in reader.fieldnames if re.search(r'train', k, re.I)]
                for row in reader:
                    for k in possible_keys:
                        val = (row.get(k) or '').strip()
                        if val:
                            train_no = re.sub(r'\D', '', val)
                            if train_no:
                                all_trains.add(train_no)
                            break
        
        missing_trains = all_trains - stored_trains
        
        return jsonify({
            "total_trains_in_dataset": len(all_trains),
            "stored_json_files": file_count, # Use rappid_count
            "missing_trains": len(missing_trains),
            "coverage_percent": round((file_count / len(all_trains) * 100) if all_trains else 0, 2),
            "last_refresh_time": last_refresh,
            "data_directory": str(json_dir),
            "sample_missing_trains": list(missing_trains)[:10]
        }), 200
    except Exception as e:
        logger.error(f"Error getting RAPPID status: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/performance-metrics', methods=['GET'])
def performance_metrics():
    """Get RAPPID client performance metrics."""
    try:
        stats = rappid_client.get_stats()
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "performance": stats,
            "server_ uptime_seconds": time.time() - app.start_time
        }), 200
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/warm-cache', methods=['POST'])
def warm_cache():
    """Warm cache with high-frequency trains."""
    try:
        from rappid_optimized import CacheWarmer
        results = CacheWarmer.warm_on_startup(rappid_client)
        return jsonify({
            "status": "success",
            "message": "Cache warming initiated",
            "results": results
        }), 200
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/clear-cache', methods=['POST'])
def clear_cache():
    """Clear RAPPID client cache."""
    try:
        rappid_client.clear_cache()
        return jsonify({
            "status": "success",
            "message": "Cache cleared"
        }), 200
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*90)
    print(" ROUTE MASTER - INTEGRATED BACKEND (RAPPID + IRCTC)")
    print(" Flask API Server with Live Train Route Optimization & Real-time Validation")
    print("="*90)
    print("\n[*] Starting backend server on http://127.0.0.1:5000")
    print("\n[*] API ENDPOINTS:")
    print("\n  ROUTE OPTIMIZATION:")
    print("   - GET /api/routes (main endpoint - returns optimized routes with validation)")
    print("     Params: origin, destination, max_transfers (default=3), date, validation (default='dual')")
    print("\n  RAPPID API INTEGRATION:")
    print("   - GET /api/train-data (get comprehensive train data)")
    print("   - GET /api/train-schedule (get detailed schedule)")
    print("   - GET /api/train-seats (get seat availability)")
    print("   - GET /api/train-fares (get fare information)")
    print("   - GET /api/train-status (get train status & delays)")
    print("   - GET /api/rappid-data/<train_no> (get stored RAPPID JSON snapshot)")
    print("   - POST /api/validate-route-rappid (validate single route)")
    print("   - POST /api/validate-routes-rappid (validate multiple routes)")
    print("\n  IRCTC API INTEGRATION:")
    print("   - GET /api/live-station (live station data)")
    print("   - GET /api/seat-availability (real-time seat info)")
    print("   - GET /api/seat-availability-by-train (seat availability with route inference)")
    print("   - GET /api/fare (train fare)")
    print("   - POST /api/validate-routes (validate routes with IRCTC)")
    print("\n  DUAL VALIDATION (RAPPID + IRCTC):")
    print("   - POST /api/validate-routes-dual (comprehensive validation from both APIs)")
    print("\n  ADMIN & MANAGEMENT:")
    print("   - POST /admin/refresh-rappid/<train_no> (refresh RAPPID data for single train)")
    print("   - POST /admin/refresh-rappid-bulk (bulk refresh for multiple trains)")
    print("   - GET /admin/status/rappid (RAPPID data status & coverage)")
    print("\n  SYSTEM:")
    print("   - GET /api/health (health check with RAPPID data stats)")
    print("\n[*] Frontend: http://localhost:5173")
    print("[*] Documentation: See RAPPID_INTEGRATION_GUIDE.md")
    print("\n[*] Features:")
    print("   [+] Real-time train schedule validation")
    print("   [+] Live seat availability checking")
    print("   [+] Dynamic fare calculation")
    print("   [+] Train status & delay monitoring")
    print("   [+] Coach composition analysis")
    print("   [+] Dual API validation (RAPPID + IRCTC)")
    print("   [+] Intelligent caching (5-minute TTL + Connection pooling)")
    print("   [+] Comprehensive error handling & retry logic")
    print("   [+] AUTO CACHE WARMING on startup (50 high-frequency trains)")
    print("   [+] Performance metrics & monitoring")
    print("="*90)
    print("\n[*] PERFORMANCE OPTIMIZATIONS (PHASE 3):")
    print("   [+] Connection pooling (10 persistent connections)")
    print("   [+] Exponential backoff retry strategy")
    print("   [+] Cache warming on startup")
    print("   [+] Performance metrics endpoint")
    print("="*90 + "\n")
    
    app.run(debug=False, port=5000)

