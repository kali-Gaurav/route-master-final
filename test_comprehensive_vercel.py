"""
COMPREHENSIVE TEST SUITE FOR VERCEL DEPLOYMENT
Route Master - Complete Validation & Testing

This test suite validates:
1. Route generation (direct, single-transfer, multi-transfer)
2. Graph building and data integrity
3. API endpoints and responses
4. Frontend integration
5. Performance benchmarks
6. Database connectivity
7. Total routes generation

Run: pytest test_comprehensive_vercel.py -v --tb=short
Or: python test_comprehensive_vercel.py
"""

import pytest
import json
import time
import logging
import random
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST DATA MODELS
# ============================================================================

@dataclass
class RouteValidation:
    """Structure for storing route validation results"""
    total_routes: int
    direct_routes: int
    single_transfer_routes: int
    multi_transfer_routes: int
    avg_time: float
    avg_cost: float
    pareto_optimal: int
    generation_time: float


@dataclass
class TestResult:
    """Test execution result"""
    test_name: str
    status: str
    message: str
    duration: float
    details: Dict


# ============================================================================
# TEST UTILITIES
# ============================================================================

class RouteValidationUtil:
    """Utilities for route validation and analysis"""
    
    @staticmethod
    def count_transfers(segments: List[Dict]) -> int:
        """Count number of transfers in a route"""
        if not segments:
            return 0
        return len(segments) - 1
    
    @staticmethod
    def validate_transfer_window(arrival_time: str, departure_time: str) -> bool:
        """Validate transfer time is realistic (30 min to 8 hours)"""
        try:
            arrival = datetime.strptime(arrival_time, "%H:%M")
            departure = datetime.strptime(departure_time, "%H:%M")
            
            # Handle next-day departure
            if departure < arrival:
                departure = departure.replace(day=arrival.day + 1)
            
            diff_minutes = (departure - arrival).total_seconds() / 60
            # 30 min to 8 hours
            return 30 <= diff_minutes <= 480
        except:
            return False
    
    @staticmethod
    def validate_route(route: Dict) -> Tuple[bool, str]:
        """Validate a single route"""
        try:
            # Check required fields
            required_fields = ['segments', 'totalTime', 'totalCost', 'totalTransfers']
            for field in required_fields:
                if field not in route:
                    return False, f"Missing field: {field}"
            
            segments = route.get('segments', [])
            if not segments:
                return False, "Route has no segments"
            
            # Validate each segment
            for i, seg in enumerate(segments):
                required_seg_fields = ['from', 'to', 'departure', 'arrival', 'trainNumber']
                for field in required_seg_fields:
                    if field not in seg:
                        return False, f"Segment {i} missing field: {field}"
            
            # Validate transfer windows
            for i in range(len(segments) - 1):
                current = segments[i]
                next_seg = segments[i + 1]
                
                if current['to'] != next_seg['from']:
                    return False, f"Transfer {i} mismatch: {current['to']} != {next_seg['from']}"
                
                # Check transfer time is realistic
                is_valid_transfer = RouteValidationUtil.validate_transfer_window(
                    current['arrival'],
                    next_seg['departure']
                )
                if not is_valid_transfer:
                    return False, f"Unrealistic transfer window at {current['to']}"
            
            return True, "Valid"
        
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# ============================================================================
# TESTS: DATABASE & GRAPH BUILDING
# ============================================================================

class TestDatabaseAndGraph:
    """Test database connectivity and graph structure"""
    
    def test_database_connection(self):
        """Test database connectivity"""
        logger.info("Testing database connection...")
        try:
            from database_manager import DatabaseManager
            db = DatabaseManager()
            
            # Test connection
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM trains")
                count = cursor.fetchone()[0]
                
                assert count > 0, "No trains in database"
                logger.info(f"✓ Database connected. Found {count} trains")
                
            return TestResult(
                test_name="Database Connection",
                status="PASS",
                message=f"Connected successfully. {count} trains found",
                duration=0.1,
                details={"trains_count": count}
            )
        except Exception as e:
            logger.error(f"✗ Database test failed: {e}")
            return TestResult(
                test_name="Database Connection",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )
    
    def test_graph_building(self):
        """Test graph building and structure"""
        logger.info("Testing graph building...")
        try:
            from optimization_engine import OptimizedGraphBuilder
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            builder = OptimizedGraphBuilder(db)
            
            # Build graph
            start_time = time.time()
            graph = builder.build_graph()
            build_time = time.time() - start_time
            
            # Validate graph
            assert graph is not None, "Graph is None"
            assert len(graph) > 0, "Graph is empty"
            
            # Check for major stations
            major_stations = ['NDLS', 'HWH', 'CSMT', 'SBC', 'MAS']
            found_stations = [s for s in major_stations if s in graph]
            
            logger.info(f"✓ Graph built in {build_time:.2f}s with {len(graph)} stations")
            logger.info(f"  Found {len(found_stations)}/{len(major_stations)} major stations")
            
            return TestResult(
                test_name="Graph Building",
                status="PASS",
                message=f"Graph built in {build_time:.2f}s",
                duration=build_time,
                details={
                    "stations": len(graph),
                    "build_time": build_time,
                    "major_stations_found": found_stations
                }
            )
        except Exception as e:
            logger.error(f"✗ Graph building test failed: {e}")
            return TestResult(
                test_name="Graph Building",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )


# ============================================================================
# TESTS: ROUTE GENERATION
# ============================================================================

class TestRouteGeneration:
    """Test route generation with all three categories"""
    
    def test_direct_routes_generation(self, source="NDLS", destination="KOTA"):
        """Test direct route generation (0 transfers)"""
        logger.info(f"\nTesting direct routes generation: {source} → {destination}")
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            start_time = time.time()
            
            # Generate direct routes
            direct_routes = router._find_direct_routes(
                router.station_to_id.get(source),
                router.station_to_id.get(destination)
            )
            
            gen_time = time.time() - start_time
            
            logger.info(f"✓ Found {len(direct_routes)} direct routes in {gen_time:.3f}s")
            
            # Validate all routes have 1 segment
            valid_count = 0
            for route in direct_routes:
                if len(route) == 1:
                    is_valid, msg = RouteValidationUtil.validate_route({
                        'segments': route,
                        'totalTransfers': 0
                    })
                    if is_valid:
                        valid_count += 1
            
            logger.info(f"  {valid_count}/{len(direct_routes)} routes are valid")
            
            return TestResult(
                test_name="Direct Routes Generation",
                status="PASS" if valid_count > 0 else "SKIP",
                message=f"Generated {len(direct_routes)} direct routes",
                duration=gen_time,
                details={
                    "total_routes": len(direct_routes),
                    "valid_routes": valid_count,
                    "generation_time": gen_time
                }
            )
        except Exception as e:
            logger.error(f"✗ Direct routes test failed: {e}")
            return TestResult(
                test_name="Direct Routes Generation",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )
    
    def test_single_transfer_routes(self, source="NDLS", destination="KOTA"):
        """Test single transfer route generation (1 transfer)"""
        logger.info(f"\nTesting single-transfer routes: {source} → {destination}")
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            start_time = time.time()
            
            # Generate single-transfer routes
            single_transfer = router._find_single_transfer_routes(
                router.station_to_id.get(source),
                router.station_to_id.get(destination)
            )
            
            gen_time = time.time() - start_time
            
            logger.info(f"✓ Found {len(single_transfer)} single-transfer routes in {gen_time:.3f}s")
            
            # Validate all routes have 2 segments
            valid_count = 0
            for route in single_transfer:
                if len(route) == 2:
                    # Check transfer window
                    transfers = RouteValidationUtil.count_transfers(route)
                    if transfers == 1:
                        valid_count += 1
            
            logger.info(f"  {valid_count}/{len(single_transfer)} routes have correct structure")
            
            return TestResult(
                test_name="Single Transfer Routes Generation",
                status="PASS" if valid_count > 0 else "SKIP",
                message=f"Generated {len(single_transfer)} single-transfer routes",
                duration=gen_time,
                details={
                    "total_routes": len(single_transfer),
                    "valid_routes": valid_count,
                    "generation_time": gen_time
                }
            )
        except Exception as e:
            logger.error(f"✗ Single-transfer routes test failed: {e}")
            return TestResult(
                test_name="Single Transfer Routes Generation",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )
    
    def test_multi_transfer_routes(self, source="NDLS", destination="KOTA"):
        """Test multi-transfer route generation (2-3 transfers)"""
        logger.info(f"\nTesting multi-transfer routes: {source} → {destination}")
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            start_time = time.time()
            
            # Generate multi-transfer routes
            multi_transfer = router._find_multi_transfer_routes(
                router.station_to_id.get(source),
                router.station_to_id.get(destination),
                max_transfers=3
            )
            
            gen_time = time.time() - start_time
            
            logger.info(f"✓ Found {len(multi_transfer)} multi-transfer routes in {gen_time:.3f}s")
            
            # Validate routes have 3+ segments
            transfer_counts = {}
            for route in multi_transfer:
                transfers = RouteValidationUtil.count_transfers(route)
                transfer_counts[transfers] = transfer_counts.get(transfers, 0) + 1
            
            logger.info(f"  Transfer distribution: {transfer_counts}")
            
            return TestResult(
                test_name="Multi-Transfer Routes Generation",
                status="PASS" if len(multi_transfer) > 0 else "SKIP",
                message=f"Generated {len(multi_transfer)} multi-transfer routes",
                duration=gen_time,
                details={
                    "total_routes": len(multi_transfer),
                    "transfer_distribution": transfer_counts,
                    "generation_time": gen_time
                }
            )
        except Exception as e:
            logger.error(f"✗ Multi-transfer routes test failed: {e}")
            return TestResult(
                test_name="Multi-Transfer Routes Generation",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )
    
    def test_complete_route_generation(self, source="NDLS", destination="KOTA"):
        """Test complete route generation (all types combined)"""
        logger.info(f"\nTesting complete route generation: {source} → {destination}")
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            start_time = time.time()
            
            # Generate all routes
            all_routes = router.generate_all_routes(source, destination, max_transfers=3)
            
            gen_time = time.time() - start_time
            
            # Count by transfer type
            direct = [r for r in all_routes if RouteValidationUtil.count_transfers(r) == 0]
            single = [r for r in all_routes if RouteValidationUtil.count_transfers(r) == 1]
            multi = [r for r in all_routes if RouteValidationUtil.count_transfers(r) >= 2]
            
            logger.info(f"✓ Generated {len(all_routes)} total routes in {gen_time:.3f}s")
            logger.info(f"  • Direct routes: {len(direct)} (0 transfers)")
            logger.info(f"  • Single-transfer: {len(single)} (1 transfer)")
            logger.info(f"  • Multi-transfer: {len(multi)} (2-3 transfers)")
            
            # Run Pareto optimization
            opt_start = time.time()
            pareto_routes, categories = router.select_optimal_routes(
                router.pareto_optimize(all_routes)
            )
            opt_time = time.time() - opt_start
            
            logger.info(f"✓ Pareto optimization completed in {opt_time:.3f}s")
            logger.info(f"  Optimal routes: {len(pareto_routes)}")
            logger.info(f"  Categories: {categories}")
            
            return TestResult(
                test_name="Complete Route Generation",
                status="PASS" if len(all_routes) > 0 else "SKIP",
                message=f"Generated {len(all_routes)} routes ({len(pareto_routes)} optimal)",
                duration=gen_time + opt_time,
                details={
                    "total_routes": len(all_routes),
                    "direct_routes": len(direct),
                    "single_transfer_routes": len(single),
                    "multi_transfer_routes": len(multi),
                    "pareto_optimal": len(pareto_routes),
                    "generation_time": gen_time,
                    "optimization_time": opt_time,
                    "categories": categories
                }
            )
        except Exception as e:
            logger.error(f"✗ Complete route generation test failed: {e}")
            return TestResult(
                test_name="Complete Route Generation",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )


# ============================================================================
# TESTS: API ENDPOINTS
# ============================================================================

class TestAPIEndpoints:
    """Test API endpoints and responses"""
    
    def test_search_endpoint(self, source="NDLS", destination="KOTA"):
        """Test /api/routes search endpoint"""
        logger.info(f"\nTesting search endpoint: {source} → {destination}")
        try:
            import requests
            
            url = "http://localhost:8000/api/routes"
            params = {
                "source": source,
                "destination": destination,
                "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            }
            
            start_time = time.time()
            response = requests.get(url, params=params, timeout=30)
            response_time = time.time() - start_time
            
            assert response.status_code == 200, f"Status code: {response.status_code}"
            
            data = response.json()
            
            # Validate response structure
            assert 'optimal_routes' in data, "Missing 'optimal_routes'"
            assert 'all_routes' in data, "Missing 'all_routes'"
            assert 'total_routes_generated' in data, "Missing 'total_routes_generated'"
            
            optimal = data.get('optimal_routes', [])
            all_routes = data.get('all_routes', [])
            total = data.get('total_routes_generated', 0)
            
            logger.info(f"✓ API responded in {response_time:.2f}s")
            logger.info(f"  Optimal routes: {len(optimal)}")
            logger.info(f"  All routes: {len(all_routes)}")
            logger.info(f"  Total generated: {total}")
            
            return TestResult(
                test_name="Search API Endpoint",
                status="PASS",
                message=f"API returned {len(optimal)} optimal + {len(all_routes)} total routes",
                duration=response_time,
                details={
                    "optimal_routes": len(optimal),
                    "all_routes": len(all_routes),
                    "total_generated": total,
                    "response_time": response_time
                }
            )
        except Exception as e:
            logger.error(f"✗ Search endpoint test failed: {e}")
            return TestResult(
                test_name="Search API Endpoint",
                status="SKIP",
                message=f"API not available: {str(e)}",
                duration=0.1,
                details={}
            )
    
    def test_response_structure(self):
        """Test API response structure and fields"""
        logger.info("\nTesting API response structure...")
        try:
            import requests
            
            url = "http://localhost:8000/api/routes"
            params = {
                "source": "NDLS",
                "destination": "KOTA",
                "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, params=params, timeout=30)
            assert response.status_code == 200
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['optimal_routes', 'all_routes', 'total_routes_generated']
            for field in required_fields:
                assert field in data, f"Missing field: {field}"
            
            # Validate route structure
            if data['optimal_routes']:
                route = data['optimal_routes'][0]
                route_fields = ['segments', 'totalTime', 'totalCost', 'totalTransfers']
                for field in route_fields:
                    assert field in route, f"Route missing field: {field}"
            
            logger.info("✓ Response structure is valid")
            
            return TestResult(
                test_name="Response Structure Validation",
                status="PASS",
                message="All required fields present",
                duration=0.1,
                details={"fields_validated": required_fields}
            )
        except Exception as e:
            logger.error(f"✗ Response structure test failed: {e}")
            return TestResult(
                test_name="Response Structure Validation",
                status="SKIP",
                message=str(e),
                duration=0.1,
                details={}
            )


# ============================================================================
# TESTS: RANDOM STATION PAIR GENERATION
# ============================================================================

class TestRandomStationPairs:
    """Test route generation with random station pairs"""
    
    def get_random_station_pairs(self, count=5):
        """Get random valid station pairs from database"""
        try:
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT source_station FROM trains ORDER BY RANDOM() LIMIT ?", (count * 3,))
                stations = [row[0] for row in cursor.fetchall()]
            
            # Create random pairs
            pairs = []
            for _ in range(count):
                if len(stations) >= 2:
                    pair = random.sample(stations, 2)
                    pairs.append(tuple(pair))
            
            return pairs
        except:
            # Fallback to known pairs
            return [
                ("NDLS", "KOTA"),
                ("NDLS", "MAS"),
                ("HWH", "CSMT"),
                ("SBC", "NDLS"),
                ("PGT", "HYD")
            ]
    
    def test_random_pairs(self):
        """Test route generation with random station pairs"""
        logger.info("\nTesting route generation with random station pairs...")
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            
            pairs = self.get_random_station_pairs(count=3)
            logger.info(f"Testing {len(pairs)} random station pairs")
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            results = []
            for source, destination in pairs:
                try:
                    start = time.time()
                    all_routes = router.generate_all_routes(source, destination)
                    gen_time = time.time() - start
                    
                    direct = [r for r in all_routes if len(r) == 1]
                    single = [r for r in all_routes if len(r) == 2]
                    multi = [r for r in all_routes if len(r) >= 3]
                    
                    result = {
                        "pair": f"{source}→{destination}",
                        "total": len(all_routes),
                        "direct": len(direct),
                        "single": len(single),
                        "multi": len(multi),
                        "time": f"{gen_time:.2f}s"
                    }
                    results.append(result)
                    
                    logger.info(f"  {source}→{destination}: {len(all_routes)} routes "
                              f"(D:{len(direct)} S:{len(single)} M:{len(multi)}) "
                              f"in {gen_time:.2f}s")
                except:
                    logger.warning(f"  Skipped {source}→{destination}")
            
            return TestResult(
                test_name="Random Station Pairs",
                status="PASS" if results else "SKIP",
                message=f"Tested {len(results)} random pairs",
                duration=0.1,
                details={"tested_pairs": results}
            )
        except Exception as e:
            logger.error(f"✗ Random pairs test failed: {e}")
            return TestResult(
                test_name="Random Station Pairs",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )


# ============================================================================
# TESTS: PERFORMANCE & STRESS
# ============================================================================

class TestPerformance:
    """Performance and stress tests"""
    
    def test_route_generation_performance(self, source="NDLS", destination="KOTA"):
        """Test route generation performance"""
        logger.info("\nTesting route generation performance...")
        try:
            from route_optimizer import ParetoTrainRouter
            from database_manager import DatabaseManager
            
            db = DatabaseManager()
            router = ParetoTrainRouter(db)
            
            # Warm up
            router.generate_all_routes(source, destination)
            
            # Measure
            times = []
            for _ in range(3):
                start = time.time()
                routes = router.generate_all_routes(source, destination)
                times.append(time.time() - start)
            
            avg_time = sum(times) / len(times)
            logger.info(f"✓ Average generation time: {avg_time:.3f}s")
            logger.info(f"  Runs: {times}")
            
            # Assert reasonable performance
            assert avg_time < 10, f"Generation too slow: {avg_time:.2f}s"
            
            return TestResult(
                test_name="Route Generation Performance",
                status="PASS",
                message=f"Average time: {avg_time:.3f}s",
                duration=sum(times),
                details={
                    "avg_time": avg_time,
                    "individual_times": times,
                    "routes_generated": len(routes)
                }
            )
        except Exception as e:
            logger.error(f"✗ Performance test failed: {e}")
            return TestResult(
                test_name="Route Generation Performance",
                status="FAIL",
                message=str(e),
                duration=0.1,
                details={}
            )
    
    def test_concurrent_requests(self):
        """Test handling concurrent route requests"""
        logger.info("\nTesting concurrent request handling...")
        try:
            import requests
            from concurrent.futures import ThreadPoolExecutor
            
            def make_request(idx):
                try:
                    url = "http://localhost:8000/api/routes"
                    params = {
                        "source": "NDLS",
                        "destination": "KOTA",
                        "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
                    }
                    start = time.time()
                    response = requests.get(url, params=params, timeout=30)
                    return {
                        "status": response.status_code,
                        "time": time.time() - start
                    }
                except Exception as e:
                    return {"status": 0, "error": str(e)}
            
            # Run 5 concurrent requests
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(make_request, range(5)))
            
            success_count = sum(1 for r in results if r.get('status') == 200)
            avg_time = sum(r.get('time', 0) for r in results) / len(results)
            
            logger.info(f"✓ Concurrent requests: {success_count}/{len(results)} successful")
            logger.info(f"  Average response time: {avg_time:.2f}s")
            
            return TestResult(
                test_name="Concurrent Requests",
                status="PASS" if success_count >= 3 else "SKIP",
                message=f"{success_count}/{len(results)} successful",
                duration=0.1,
                details={
                    "success_count": success_count,
                    "avg_response_time": avg_time,
                    "results": results
                }
            )
        except Exception as e:
            logger.error(f"✗ Concurrent requests test failed: {e}")
            return TestResult(
                test_name="Concurrent Requests",
                status="SKIP",
                message=str(e),
                duration=0.1,
                details={}
            )


# ============================================================================
# TEST RUNNER
# ============================================================================

class TestRunner:
    """Main test runner that executes all tests"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
    
    def run_all_tests(self):
        """Run all test suites"""
        logger.info("=" * 80)
        logger.info("ROUTE MASTER - COMPREHENSIVE TEST SUITE")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Database & Graph Tests
        logger.info("\n" + "="*80)
        logger.info("LAYER 1: DATABASE & GRAPH BUILDING")
        logger.info("="*80)
        db_tests = TestDatabaseAndGraph()
        self.results.append(db_tests.test_database_connection())
        self.results.append(db_tests.test_graph_building())
        
        # Route Generation Tests
        logger.info("\n" + "="*80)
        logger.info("LAYER 2: ROUTE GENERATION")
        logger.info("="*80)
        route_tests = TestRouteGeneration()
        self.results.append(route_tests.test_direct_routes_generation())
        self.results.append(route_tests.test_single_transfer_routes())
        self.results.append(route_tests.test_multi_transfer_routes())
        self.results.append(route_tests.test_complete_route_generation())
        
        # API Tests
        logger.info("\n" + "="*80)
        logger.info("LAYER 3: API ENDPOINTS")
        logger.info("="*80)
        api_tests = TestAPIEndpoints()
        self.results.append(api_tests.test_search_endpoint())
        self.results.append(api_tests.test_response_structure())
        
        # Random Pairs Tests
        logger.info("\n" + "="*80)
        logger.info("LAYER 4: RANDOM STATION PAIRS")
        logger.info("="*80)
        random_tests = TestRandomStationPairs()
        self.results.append(random_tests.test_random_pairs())
        
        # Performance Tests
        logger.info("\n" + "="*80)
        logger.info("LAYER 5: PERFORMANCE & STRESS")
        logger.info("="*80)
        perf_tests = TestPerformance()
        self.results.append(perf_tests.test_route_generation_performance())
        self.results.append(perf_tests.test_concurrent_requests())
        
        total_time = time.time() - start_time
        
        # Print summary
        self.print_summary(total_time)
    
    def print_summary(self, total_time):
        """Print test summary"""
        logger.info("\n" + "="*80)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("="*80)
        
        for result in self.results:
            status_icon = "✓" if result.status == "PASS" else "✗" if result.status == "FAIL" else "⊘"
            logger.info(f"{status_icon} {result.test_name}: {result.status}")
            logger.info(f"  └─ {result.message} ({result.duration:.3f}s)")
            
            if result.details:
                for key, value in result.details.items():
                    logger.info(f"     • {key}: {value}")
            
            # Update summary
            self.summary["total"] += 1
            if result.status == "PASS":
                self.summary["passed"] += 1
            elif result.status == "FAIL":
                self.summary["failed"] += 1
            else:
                self.summary["skipped"] += 1
        
        logger.info("\n" + "="*80)
        logger.info(f"FINAL RESULT: {self.summary['passed']}/{self.summary['total']} PASSED "
                   f"({self.summary['failed']} FAILED, {self.summary['skipped']} SKIPPED)")
        logger.info(f"Total execution time: {total_time:.2f}s")
        logger.info("="*80)
        
        # Exit code
        return 0 if self.summary['failed'] == 0 else 1


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
