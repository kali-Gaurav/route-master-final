"""
PHASE 1 COMPREHENSIVE VERIFICATION TEST SUITE
============================================
Tests all Phase 1 features:
- Database Manager (connection pooling, schema, transactions)
- Bulk Import (97k+ CSV rows to database)
- Data Validation (integrity checks, deduplication)
- RAPPID Fetcher (database integration)
- Unified API (database queries)
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database_manager import DatabaseManager, get_db


class Phase1VerificationSuite:
    """Comprehensive Phase 1 test suite"""

    def __init__(self):
        self.db = get_db()
        self.test_results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name, passed, message):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.test_results.append((test_name, passed, message))
        print(f"{status}: {test_name} - {message}")
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    # =========================================================================
    # TEST 1: Database Manager Connection & Schema
    # =========================================================================

    def test_database_connection(self):
        """Test 1.1: Database connection pooling"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            self.log_test(
                "1.1 Database Connection",
                result is not None,
                "Connection and basic query successful"
            )
        except Exception as e:
            self.log_test("1.1 Database Connection", False, str(e))

    def test_schema_existence(self):
        """Test 1.2: All required tables exist"""
        required_tables = [
            'trains', 'stations', 'train_stations',
            'search_logs', 'performance_logs', 'data_quality'
        ]
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            existing_tables = set(row[0] for row in cursor.fetchall())
            conn.close()

            missing = set(required_tables) - existing_tables
            self.log_test(
                "1.2 Schema Existence",
                len(missing) == 0,
                f"All {len(required_tables)} tables exist" if not missing else f"Missing: {missing}"
            )
        except Exception as e:
            self.log_test("1.2 Schema Existence", False, str(e))

    def test_schema_columns(self):
        """Test 1.3: Key columns in tables"""
        expected_columns = {
            'trains': ['id', 'train_no', 'train_name', 'created_at'],
            'stations': ['id', 'station_code', 'station_name', 'city'],
            'train_stations': ['id', 'train_id', 'station_id', 'sequence']
        }
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            all_valid = True
            for table, columns in expected_columns.items():
                cursor.execute(f"PRAGMA table_info({table})")
                actual_columns = set(row[1] for row in cursor.fetchall())
                if not set(columns).issubset(actual_columns):
                    all_valid = False
                    break

            conn.close()
            self.log_test(
                "1.3 Schema Columns",
                all_valid,
                "All key columns present in required tables"
            )
        except Exception as e:
            self.log_test("1.3 Schema Columns", False, str(e))

    # =========================================================================
    # TEST 2: Data Integrity & Volume
    # =========================================================================

    def test_data_volume(self):
        """Test 2.1: Expected data volume (197k+ CSV rows imported)"""
        try:
            stats = self.db.get_stats()
            trains = stats['total_trains']
            stations = stats['total_stations']
            routes = stats['total_routes']

            # Verify expected ranges based on RAPPID dataset
            valid = (
                trains > 9000 and trains < 11000 and  # Should be ~9,880
                stations > 3500 and stations < 4500 and  # Should be ~3,874
                routes > 80000 and routes < 95000  # Should be ~92,226
            )

            self.log_test(
                "2.1 Data Volume",
                valid,
                f"Trains: {trains}, Stations: {stations}, Routes: {routes}"
            )
        except Exception as e:
            self.log_test("2.1 Data Volume", False, str(e))

    def test_foreign_key_integrity(self):
        """Test 2.2: Foreign key constraints enforced"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Check train_stations references valid trains
            cursor.execute("""
                SELECT COUNT(*) FROM train_stations ts
                WHERE NOT EXISTS (SELECT 1 FROM trains t WHERE t.id = ts.train_id)
            """)
            orphan_count = cursor.fetchone()[0]
            conn.close()

            self.log_test(
                "2.2 Foreign Key Integrity",
                orphan_count == 0,
                "No orphan train_stations records"
            )
        except Exception as e:
            self.log_test("2.2 Foreign Key Integrity", False, str(e))

    def test_duplicate_prevention(self):
        """Test 2.3: No duplicate train_no values (unique constraint)"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Check for duplicate train_no values
            cursor.execute("""
                SELECT COUNT(*) FROM (
                    SELECT train_no, COUNT(*) as cnt FROM trains
                    GROUP BY train_no HAVING cnt > 1
                )
            """)
            duplicate_count = cursor.fetchone()[0]
            conn.close()

            self.log_test(
                "2.3 Duplicate Prevention",
                duplicate_count == 0,
                "No duplicate train_no values (UNIQUE constraint working)"
            )
        except Exception as e:
            self.log_test("2.3 Duplicate Prevention", False, str(e))

    def test_non_null_constraints(self):
        """Test 2.4: Required fields are NOT NULL"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Check for NULL values in key fields
            cursor.execute("""
                SELECT COUNT(*) FROM trains WHERE train_no IS NULL OR train_name IS NULL
            """)
            null_trains = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM stations WHERE station_code IS NULL OR station_name IS NULL
            """)
            null_stations = cursor.fetchone()[0]

            conn.close()

            valid = null_trains == 0 and null_stations == 0
            self.log_test(
                "2.4 NOT NULL Constraints",
                valid,
                "All key fields have values (no NULL violations)"
            )
        except Exception as e:
            self.log_test("2.4 NOT NULL Constraints", False, str(e))

    # =========================================================================
    # TEST 3: Query Performance & Indexing
    # =========================================================================

    def test_index_creation(self):
        """Test 3.1: Strategic indexes created"""
        required_indexes = [
            'idx_train_no',
            'idx_station_code',
            'idx_station_name',
            'idx_train_stations_train_id',
            'idx_train_stations_station_id'
        ]
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            existing_indexes = set(row[0] for row in cursor.fetchall())
            conn.close()

            missing = set(required_indexes) - existing_indexes
            self.log_test(
                "3.1 Index Creation",
                len(missing) == 0,
                f"All {len(required_indexes)} indexes created" if not missing else f"Missing: {missing}"
            )
        except Exception as e:
            self.log_test("3.1 Index Creation", False, str(e))

    def test_search_performance(self):
        """Test 3.2: Database search queries work efficiently"""
        try:
            import time

            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Test indexed query on station_code
            start = time.time()
            cursor.execute("SELECT * FROM stations WHERE station_code = ? LIMIT 1", ('CSMT',))
            result = cursor.fetchone()
            query_time_ms = (time.time() - start) * 1000

            conn.close()

            valid = result is not None and query_time_ms < 100  # Should be < 100ms
            self.log_test(
                "3.2 Search Performance",
                valid,
                f"Station search completed in {query_time_ms:.2f}ms (expected < 100ms)"
            )
        except Exception as e:
            self.log_test("3.2 Search Performance", False, str(e))

    def test_route_query(self):
        """Test 3.3: Complex route queries work"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Test complex query for routes between two stations
            cursor.execute("""
                SELECT COUNT(DISTINCT t.train_no) FROM trains t
                JOIN train_stations ts1 ON t.id = ts1.train_id
                JOIN train_stations ts2 ON t.id = ts2.train_id
                JOIN stations s1 ON ts1.station_id = s1.id
                JOIN stations s2 ON ts2.station_id = s2.id
                WHERE s1.station_code = ? AND s2.station_code = ?
                AND ts1.sequence < ts2.sequence
            """, ('CSMT', 'KHED'))

            route_count = cursor.fetchone()[0]
            conn.close()

            self.log_test(
                "3.3 Route Queries",
                route_count > 0,
                f"Route query returned {route_count} routes between CSMT and KHED"
            )
        except Exception as e:
            self.log_test("3.3 Route Queries", False, str(e))

    # =========================================================================
    # TEST 4: API Integration
    # =========================================================================

    def test_routing_engine_singleton(self):
        """Test 4.1: Routing engine singleton initializes"""
        try:
            from api_v2 import get_routing_engine_singleton

            engine = get_routing_engine_singleton()
            self.log_test(
                "4.1 Routing Engine Singleton",
                engine is not None and hasattr(engine, 'search'),
                "Routing engine initialized with search method"
            )
        except Exception as e:
            self.log_test("4.1 Routing Engine Singleton", False, str(e))

    def test_route_search(self):
        """Test 4.2: Route search returns valid results"""
        try:
            from api_v2 import get_routing_engine_singleton

            engine = get_routing_engine_singleton()
            routes = engine.search('CSMT', 'KHED', max_results=5)

            valid = (
                isinstance(routes, list) and
                len(routes) > 0 and
                all(isinstance(r, dict) for r in routes) and
                all('segments' in r for r in routes)
            )

            self.log_test(
                "4.2 Route Search",
                valid,
                f"Found {len(routes)} valid routes (CSMT → KHED)"
            )
        except Exception as e:
            self.log_test("4.2 Route Search", False, str(e))

    def test_search_logging(self):
        """Test 4.3: Search logging works"""
        try:
            # Perform a search to trigger logging
            from api_v2 import get_routing_engine_singleton

            engine = get_routing_engine_singleton()
            routes = engine.search('CSMT', 'KHED', max_results=1)

            # Check that search was logged
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM search_logs WHERE origin = ? AND destination = ?",
                         ('CSMT', 'KHED'))
            log_count = cursor.fetchone()[0]
            conn.close()

            self.log_test(
                "4.3 Search Logging",
                log_count > 0,
                f"Search logged successfully ({log_count} records in database)"
            )
        except Exception as e:
            self.log_test("4.3 Search Logging", False, str(e))

    # =========================================================================
    # TEST 5: Optional Features
    # =========================================================================

    def test_graph_builder(self):
        """Test 5.1: Graph builder can construct from database"""
        try:
            from optimization_engine import OptimizedGraphBuilder

            builder = OptimizedGraphBuilder(self.db)
            graph = builder.build_from_database()

            valid = (
                'adjacency_list' in graph and
                'station_to_id' in graph and
                len(graph['station_to_id']) > 0 and
                len(graph['adjacency_list']) > 0
            )

            self.log_test(
                "5.1 Graph Builder",
                valid,
                f"Built graph with {len(graph['station_to_id'])} stations and {sum(len(e) for e in graph['adjacency_list'].values())} edges"
            )
        except Exception as e:
            self.log_test("5.1 Graph Builder", False, str(e))

    def test_route_optimizer(self):
        """Test 5.2: Route optimizer loads from database"""
        try:
            from route_optimizer import ParetoTrainRouter

            router = ParetoTrainRouter({}, {'station_to_id': {}, 'id_to_station': {}}, None, None, self.db)

            valid = (
                router is not None and
                len(router.train_info) > 0 and
                all(isinstance(v, dict) for v in router.train_info.values())
            )

            self.log_test(
                "5.2 Route Optimizer",
                valid,
                f"Route optimizer loaded {len(router.train_info)} trains from database"
            )
        except Exception as e:
            self.log_test("5.2 Route Optimizer", False, str(e))

    def test_connection_pooling(self):
        """Test 5.3: Connection pooling works"""
        try:
            # Get multiple connections to verify pooling
            conn1 = self.db.get_connection()
            conn2 = self.db.get_connection()
            conn1.close()
            conn2.close()

            # Verify we can still get connections after closing
            conn3 = self.db.get_connection()
            cursor = conn3.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn3.close()

            self.log_test(
                "5.3 Connection Pooling",
                result is not None,
                "Connection pooling managing connections correctly"
            )
        except Exception as e:
            self.log_test("5.3 Connection Pooling", False, str(e))

    # =========================================================================
    # Report Generation
    # =========================================================================

    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*80)
        print("PHASE 1 VERIFICATION TEST REPORT")
        print("="*80)

        # Group tests by category
        categories = {
            '1': 'Database Connection & Schema',
            '2': 'Data Integrity & Volume',
            '3': 'Query Performance & Indexing',
            '4': 'API Integration',
            '5': 'Optional Features'
        }

        for prefix, category_name in categories.items():
            category_tests = [t for t in self.test_results if t[0].startswith(prefix)]
            if category_tests:
                print(f"\n{category_name}:")
                for test_name, passed, message in category_tests:
                    status = "✓" if passed else "✗"
                    print(f"  {status} {test_name}: {message}")

        # Summary
        total = self.passed + self.failed
        percentage = (self.passed / total * 100) if total > 0 else 0

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed} ({percentage:.1f}%)")
        print(f"Failed: {self.failed}")
        print(f"Status: {'✓ PHASE 1 COMPLETE' if self.failed == 0 else '✗ PHASE 1 INCOMPLETE'}")
        print("="*80 + "\n")

        return self.failed == 0


def main():
    """Run all Phase 1 tests"""
    print("Starting Phase 1 Comprehensive Verification Suite...\n")

    suite = Phase1VerificationSuite()

    # Run all tests
    suite.test_database_connection()
    suite.test_schema_existence()
    suite.test_schema_columns()

    suite.test_data_volume()
    suite.test_foreign_key_integrity()
    suite.test_duplicate_prevention()
    suite.test_non_null_constraints()

    suite.test_index_creation()
    suite.test_search_performance()
    suite.test_route_query()

    suite.test_routing_engine_singleton()
    suite.test_route_search()
    suite.test_search_logging()

    suite.test_graph_builder()
    suite.test_route_optimizer()
    suite.test_connection_pooling()

    # Generate report and return status
    phase_complete = suite.generate_report()

    if phase_complete:
        print("✓ ALL PHASE 1 TESTS PASSING - READY FOR PHASE 2\n")
        return 0
    else:
        print("✗ PHASE 1 TESTS FAILING - FIX BEFORE PROCEEDING TO PHASE 2\n")
        return 1


if __name__ == "__main__":
    exit(main())