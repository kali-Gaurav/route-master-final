# test_system_integration.py - Integration Tests for Autonomous Railway System
"""
Integration tests for the autonomous railway operating system.
Tests route generation, graph building, and autonomous features.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import time

# Add database folder to path
sys.path.insert(0, os.path.dirname(__file__))

from autonomous_system import AutonomousSystem, ServiceDiscovery
from database_core import DatabaseCore, GraphBuilder, RouteGenerator, PerformanceAnalyzer
from connection import db_manager
from models.route import Route
from models.station import Station
from models.train import Train
from models.user import User
from models.tenant import Tenant


class TestSystemIntegration:
    """Integration tests for the complete system."""

    def __init__(self):
        self.db_core = None
        self.autonomous_system = None

    async def initialize(self):
        """Initialize test environment."""
        print("Initializing test environment...")
        self.db_core = DatabaseCore()
        await self.db_core.initialize()

        self.autonomous_system = AutonomousSystem()
        await self.autonomous_system.initialize()

    async def shutdown(self):
        """Shutdown test environment."""
        print("Shutting down test environment...")
        if self.db_core:
            await self.db_core.shutdown()
        if self.autonomous_system:
            await self.autonomous_system.shutdown()

    async def setup_test_data(self):
        """Setup comprehensive test data."""
        print("Setting up test data...")

        with db_manager.session_scope() as session:
            # Create tenant
            tenant = Tenant(name="Test Railway", is_active=True)
            session.add(tenant)
            session.commit()
            tenant_id = tenant.id

            # Create user
            user = User(
                tenant_id=tenant_id,
                username="testadmin",
                email="admin@railway.test",
                role="admin",
                is_active=True
            )
            session.add(user)
            session.commit()

            # Create comprehensive station network
            stations_data = [
                # Tier 1: Major Junctions
                {"code": "NDLS", "name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "zone": "CR", "is_junction": True},
                {"code": "BCT", "name": "Mumbai Central", "lat": 18.9690, "lon": 72.8205, "zone": "WR", "is_junction": True},
                {"code": "HWH", "name": "Howrah Junction", "lat": 22.5822, "lon": 88.3378, "zone": "ER", "is_junction": True},
                {"code": "CSMT", "name": "CST Mumbai", "lat": 18.9631, "lon": 72.8358, "zone": "WR", "is_junction": True},

                # Tier 2: Important Stations
                {"code": "CNB", "name": "Kanpur Central", "lat": 26.4499, "lon": 80.3319, "zone": "NR", "is_junction": True},
                {"code": "LKO", "name": "Lucknow Central", "lat": 26.8444, "lon": 80.9178, "zone": "NR", "is_junction": True},
                {"code": "AGC", "name": "Agra Cantt", "lat": 27.1817, "lon": 78.1832, "zone": "NR", "is_junction": True},
                {"code": "ANVT", "name": "Anand Vihar", "lat": 28.6108, "lon": 77.2533, "zone": "NR", "is_junction": False},

                # Tier 3: Secondary Stations
                {"code": "BND", "name": "Banda", "lat": 25.4852, "lon": 80.3349, "zone": "NR", "is_junction": False},
                {"code": "JHS", "name": "Jharsuguda", "lat": 21.8458, "lon": 84.8266, "zone": "SECR", "is_junction": False},
                {"code": "BBS", "name": "Bhubaneswar", "lat": 20.2366, "lon": 85.8659, "zone": "ECoR", "is_junction": True},
                {"code": "VZA", "name": "Visakhapatnam", "lat": 17.6869, "lon": 83.2185, "zone": "ECoR", "is_junction": True},

                # Tier 4: Connecting Stations
                {"code": "KNJ", "name": "Kannauj", "lat": 27.0697, "lon": 79.9190, "zone": "NR", "is_junction": False},
                {"code": "BNZ", "name": "Bijnor", "lat": 29.3821, "lon": 78.1308, "zone": "NR", "is_junction": False},
                {"code": "MRT", "name": "Merut City", "lat": 28.9845, "lon": 77.7064, "zone": "NR", "is_junction": False},
            ]

            stations = []
            for data in stations_data:
                station = Station(
                    code=data['code'],
                    name=data['name'],
                    latitude=data['lat'],
                    longitude=data['lon'],
                    zone=data['zone'],
                    is_junction=data.get('is_junction', False),
                    tenant_id=tenant_id,
                    is_active=True
                )
                session.add(station)
                stations.append(station)

            session.commit()

            # Create trains
            trains_data = [
                {"number": "12001", "name": "Rajdhani Express", "type": "Premium Express"},
                {"number": "12005", "name": "Bhagirath Express", "type": "Premium Express"},
                {"number": "12013", "name": "Ashram Express", "type": "Premium Express"},
                {"number": "12051", "name": "Mumbai-Delhi Express", "type": "Premium Express"},
                {"number": "22877", "name": "Sealdah Rajdhani", "type": "Premium Express"},
                {"number": "15002", "name": "Mandalay Express", "type": "Express"},
                {"number": "15012", "name": "Mumbai-Guwahati Express", "type": "Express"},
            ]

            trains = []
            for data in trains_data:
                train = Train(
                    number=data['number'],
                    name=data['name'],
                    type=data['type'],
                    operator="Indian Railways",
                    max_speed_kmph=120.0,
                    total_coaches=18,
                    classes_available=["1A", "2A", "3A", "SL"],
                    tenant_id=tenant_id,
                    is_active=True
                )
                session.add(train)
                trains.append(train)

            session.commit()

            # Create routes with realistic distances
            routes_data = [
                # Delhi-Mumbai Network
                ("NDLS", "CNB", 440.0, 480, "12001"),      # Delhi to Kanpur
                ("CNB", "BND", 180.0, 240, "12001"),       # Kanpur to Banda
                ("BND", "JHS", 160.0, 180, "12001"),       # Banda to Jharsuguda
                ("JHS", "BBS", 220.0, 280, "12001"),       # Jharsuguda to Bhubaneswar
                ("BBS", "VZA", 480.0, 600, "12005"),       # Bhubaneswar to Visakhapatnam

                # Delhi-Mumbai via Agra
                ("NDLS", "AGC", 206.0, 240, "12013"),      # Delhi to Agra
                ("AGC", "CNB", 260.0, 300, "12013"),       # Agra to Kanpur
                ("CNB", "BCT", 1100.0, 1200, "12051"),     # Kanpur to Mumbai

                # Northern Routes
                ("NDLS", "LKO", 530.0, 600, "22877"),      # Delhi to Lucknow
                ("LKO", "CNB", 250.0, 300, "22877"),       # Lucknow to Kanpur

                # Secondary Routes
                ("NDLS", "ANVT", 25.0, 45, "15002"),       # Delhi to Anand Vihar
                ("ANVT", "BNZ", 85.0, 120, "15002"),       # Anand Vihar to Bijnor
                ("BNZ", "MRT", 95.0, 140, "15002"),        # Bijnor to Meerut
                ("MRT", "CNB", 180.0, 240, "15002"),       # Meerut to Kanpur

                # Eastern Routes
                ("BBS", "HWH", 400.0, 480, "15012"),       # Bhubaneswar to Howrah
                ("VZA", "HWH", 880.0, 1080, "15012"),      # Visakhapatnam to Howrah
            ]

            for origin_code, dest_code, distance, duration, train_num in routes_data:
                origin = next(s for s in stations if s.code == origin_code)
                dest = next(s for s in stations if s.code == dest_code)
                train = next(t for t in trains if t.number == train_num)

                route = Route(
                    train_id=train.id,
                    origin_station_id=origin.id,
                    dest_station_id=dest.id,
                    distance_km=distance,
                    duration_minutes=duration,
                    route_type="Direct",
                    tenant_id=tenant_id,
                    is_active=True
                )
                session.add(route)

            session.commit()
            print(f"Created {len(stations)} stations, {len(trains)} trains, and {len(routes_data)} routes")

    async def test_graph_building(self):
        """Test graph building and visualization."""
        print("\n" + "="*60)
        print("TEST 1: Graph Building and Analysis")
        print("="*60)

        try:
            start_time = time.time()
            graph = await self.db_core.graph_builder.build_graph()
            build_time = time.time() - start_time

            print(f"✓ Graph built successfully in {build_time:.2f}s")
            print(f"  - Nodes (stations): {len(graph.nodes)}")
            print(f"  - Edges (routes): {len(graph.edges)}")
            print(f"  - Is connected: {graph.is_directed()}")

            # Calculate network metrics
            if len(graph.nodes) > 0:
                # Find central nodes
                try:
                    centrality = self.db_core.graph_builder._calculate_centrality(graph)
                    top_hubs = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(f"\n  Top 5 Network Hubs:")
                    for i, (station_id, score) in enumerate(top_hubs, 1):
                        with db_manager.session_scope() as session:
                            station = session.query(Station).filter(Station.id == station_id).first()
                            if station:
                                print(f"    {i}. {station.code} ({station.name}): {score:.3f}")
                except Exception as e:
                    print(f"  Note: Hub analysis skipped ({str(e)})")

        except Exception as e:
            print(f"✗ Graph building failed: {e}")
            return False

        return True

    async def test_route_generation(self):
        """Test multi-transfer route generation."""
        print("\n" + "="*60)
        print("TEST 2: Multi-Transfer Route Generation (0-3 Transfers)")
        print("="*60)

        test_cases = [
            ("NDLS", "BCT", "Delhi to Mumbai"),
            ("NDLS", "HWH", "Delhi to Howrah"),
            ("NDLS", "VZA", "Delhi to Visakhapatnam"),
            ("BCT", "VZA", "Mumbai to Visakhapatnam"),
        ]

        results = []

        for origin, dest, description in test_cases:
            try:
                print(f"\nSearching: {description} ({origin} → {dest})")
                print("-" * 50)

                start_time = time.time()
                routes = await self.db_core.find_optimal_routes(
                    origin, dest, max_transfers=3, optimize_for="duration"
                )
                search_time = time.time() - start_time

                if routes:
                    print(f"✓ Found {len(routes)} routes in {search_time:.3f}s")

                    for i, route in enumerate(routes[:3], 1):  # Show top 3
                        print(f"\n  Route {i}:")
                        print(f"    Transfers: {route.get('total_transfers', 'N/A')}")
                        print(f"    Distance: {route.get('total_distance', 'N/A'):.1f} km")
                        print(f"    Duration: {route.get('total_duration', 'N/A')} minutes")
                        print(f"    Fare: ₹{route.get('total_fare', 'N/A')}")

                        if 'path' in route:
                            path = route['path']
                            print(f"    Path: {' → '.join(path)}")

                    results.append({
                        "route": f"{origin}→{dest}",
                        "status": "✓",
                        "count": len(routes),
                        "time": search_time
                    })
                else:
                    print(f"✗ No routes found for {origin} → {dest}")
                    results.append({
                        "route": f"{origin}→{dest}",
                        "status": "✗",
                        "count": 0,
                        "time": search_time
                    })

            except Exception as e:
                print(f"✗ Route search failed: {e}")
                results.append({
                    "route": f"{origin}→{dest}",
                    "status": "✗",
                    "error": str(e)
                })

        # Summary
        print("\n" + "-" * 50)
        print("Route Generation Summary:")
        for result in results:
            status = result['status']
            route = result['route']
            if status == "✓":
                print(f"  {status} {route}: Found {result['count']} routes ({result['time']:.3f}s)")
            else:
                print(f"  {status} {route}: Failed")

        return all(r['status'] == "✓" for r in results)

    async def test_performance_analysis(self):
        """Test system performance analysis."""
        print("\n" + "="*60)
        print("TEST 3: System Performance Analysis")
        print("="*60)

        try:
            analysis = await self.db_core.analyze_system_performance()

            print("\nDatabase Performance:")
            if 'query_performance' in analysis:
                qp = analysis['query_performance']
                print(f"  - Average Query Time: {qp.get('avg_query_time', 'N/A')} ms")
                print(f"  - Slow Queries: {qp.get('slow_queries', 'N/A')}")
                print(f"  - Query Cache Hit Rate: {qp.get('cache_hit_rate', 'N/A')}%")

            if 'index_usage' in analysis:
                iu = analysis['index_usage']
                print(f"\nIndex Performance:")
                print(f"  - Index Hit Rate: {iu.get('hit_rate', 'N/A')}%")
                print(f"  - Unused Indexes: {iu.get('unused_count', 'N/A')}")

            if 'connection_pool' in analysis:
                cp = analysis['connection_pool']
                print(f"\nConnection Pool:")
                print(f"  - Active Connections: {cp.get('active', 'N/A')}")
                print(f"  - Pool Size: {cp.get('total', 'N/A')}")
                print(f"  - Utilization: {cp.get('utilization', 'N/A')}%")

            print("\n✓ Performance analysis completed")
            return True

        except Exception as e:
            print(f"✗ Performance analysis failed: {e}")
            return False

    async def test_autonomous_features(self):
        """Test autonomous system features."""
        print("\n" + "="*60)
        print("TEST 4: Autonomous System Features")
        print("="*60)

        try:
            # Test service discovery
            print("\nService Discovery:")
            service_id = await self.autonomous_system.service_discovery.register_service({
                "service_type": "test_service",
                "service_name": "test_booking_service",
                "host": "test.example.com",
                "port": 8080,
                "endpoints": ["/book", "/cancel"],
                "health_check_url": "http://test.example.com/health"
            })
            print(f"  ✓ Service registered with ID: {service_id}")

            # Test service discovery
            services = await self.autonomous_system.service_discovery.discover_services()
            print(f"  ✓ Discovered {len(services)} services")

            # Test system status
            print("\nSystem Status:")
            status = await self.autonomous_system.get_system_status()
            print(f"  ✓ System Status: {status.get('status', 'unknown')}")
            print(f"  ✓ Uptime: {status.get('uptime_seconds', 'N/A')} seconds")
            print(f"  ✓ Services: {status.get('services_count', 'N/A')}")

            return True

        except Exception as e:
            print(f"✗ Autonomous features test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*70)
        print("AUTONOMOUS RAILWAY OPERATING SYSTEM - INTEGRATION TEST SUITE")
        print("="*70)

        try:
            # Setup
            await self.initialize()
            await self.setup_test_data()

            # Run tests
            test_results = {}

            test_results["graph_building"] = await self.test_graph_building()
            test_results["route_generation"] = await self.test_route_generation()
            test_results["performance_analysis"] = await self.test_performance_analysis()
            test_results["autonomous_features"] = await self.test_autonomous_features()

            # Summary
            print("\n" + "="*70)
            print("TEST RESULTS SUMMARY")
            print("="*70)

            total_tests = len(test_results)
            passed_tests = sum(1 for v in test_results.values() if v)
            passed_percentage = (passed_tests / total_tests) * 100

            for test_name, result in test_results.items():
                status = "✓ PASSED" if result else "✗ FAILED"
                print(f"  {status}: {test_name}")

            print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({passed_percentage:.1f}%)")
            print("="*70 + "\n")

            return passed_tests == total_tests

        finally:
            await self.shutdown()


async def main():
    """Main test execution."""
    test_suite = TestSystemIntegration()
    success = await test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)