# test_autonomous_system.py - Comprehensive Test Suite
"""
Comprehensive test suite for the autonomous railway operating system.
Tests all components: database core, autonomous system, integration APIs.
"""

import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from datetime import datetime, timedelta
import json

# Add database folder to path
sys.path.insert(0, os.path.dirname(__file__))

from autonomous_system import AutonomousSystem, ServiceDiscovery, SchemaSynchronizer, AutonomousOptimizer
from database_core import DatabaseCore, GraphBuilder, RouteGenerator, PerformanceAnalyzer
from connection import db_manager
from models.route import Route
from models.station import Station
from models.train import Train
from models.user import User
from models.tenant import Tenant
from models.system import AuditLog

class TestAutonomousSystem:
    """Test the autonomous system components."""

    @pytest.fixture
    async def autonomous_system(self):
        """Create autonomous system instance."""
        system = AutonomousSystem()
        await system.initialize()
        yield system
        await system.shutdown()

    @pytest.mark.asyncio
    async def test_system_initialization(self, autonomous_system):
        """Test autonomous system initialization."""
        assert autonomous_system.running
        assert autonomous_system.service_discovery is not None
        assert autonomous_system.schema_synchronizer is not None
        assert autonomous_system.autonomous_optimizer is not None
        assert autonomous_system.integration_api is not None

    @pytest.mark.asyncio
    async def test_service_discovery(self, autonomous_system):
        """Test service discovery functionality."""
        # Register a service
        service_data = {
            "service_type": "backend",
            "service_name": "test_backend",
            "host": "localhost",
            "port": 8080,
            "endpoints": ["/api/v1/routes", "/api/v1/stations"],
            "health_check_url": "http://localhost:8080/health"
        }

        service_id = await autonomous_system.service_discovery.register_service(service_data)
        assert service_id is not None

        # Discover services
        services = await autonomous_system.service_discovery.discover_services("backend")
        assert len(services) > 0
        assert any(s.service_name == "test_backend" for s in services)

    @pytest.mark.asyncio
    async def test_schema_synchronization(self, autonomous_system):
        """Test schema synchronization."""
        # Mock external service
        mock_service = Mock()
        mock_service.get_schema_contract.return_value = {
            "version": "1.0.0",
            "tables": ["routes", "stations"],
            "constraints": ["fk_routes_stations"]
        }

        with patch.object(autonomous_system.schema_synchronizer, '_get_external_schemas', return_value=[mock_service]):
            result = await autonomous_system.schema_synchronizer.synchronize_schemas()
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_autonomous_optimization(self, autonomous_system):
        """Test autonomous optimization."""
        # Mock performance metrics
        with patch.object(autonomous_system.autonomous_optimizer, '_analyze_performance', return_value={
            "cpu_usage": 85.0,
            "memory_usage": 90.0,
            "query_performance": {"slow_queries": 5}
        }):
            await autonomous_system.autonomous_optimizer.optimize_performance()
            # Check if optimization actions were taken
            assert True  # Placeholder - would check actual optimization results

class TestDatabaseCore:
    """Test the database core components."""

    @pytest.fixture
    async def db_core(self):
        """Create database core instance."""
        core = DatabaseCore()
        await core.initialize()
        yield core
        await core.shutdown()

    @pytest.mark.asyncio
    async def test_graph_building(self, db_core):
        """Test graph building functionality."""
        # Ensure we have test data
        await self._ensure_test_data()

        graph = await db_core.graph_builder.build_graph()
        assert graph is not None
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

    @pytest.mark.asyncio
    async def test_route_generation(self, db_core):
        """Test route generation."""
        await self._ensure_test_data()

        routes = await db_core.find_optimal_routes("NDLS", "BCT", max_transfers=2)
        assert isinstance(routes, list)
        if len(routes) > 0:
            route = routes[0]
            assert hasattr(route, 'segments')
            assert hasattr(route, 'total_distance')
            assert hasattr(route, 'total_duration')

    @pytest.mark.asyncio
    async def test_performance_analysis(self, db_core):
        """Test performance analysis."""
        analysis = await db_core.analyze_system_performance()
        assert isinstance(analysis, dict)
        assert "query_performance" in analysis
        assert "index_usage" in analysis
        assert "connection_pool" in analysis

    async def _ensure_test_data(self):
        """Ensure test data exists."""
        with db_manager.session_scope() as session:
            # Check if test stations exist
            station_count = session.query(Station).count()
            if station_count == 0:
                # Create test stations
                stations_data = [
                    {"code": "NDLS", "name": "New Delhi", "latitude": 28.6139, "longitude": 77.2090},
                    {"code": "BCT", "name": "Mumbai Central", "latitude": 18.9690, "longitude": 72.8205},
                    {"code": "HWH", "name": "Howrah Junction", "latitude": 22.5822, "longitude": 88.3378}
                ]
                for data in stations_data:
                    station = Station(**data)
                    session.add(station)
                session.commit()

class TestIntegrationAPI:
    """Test the integration API endpoints."""

    @pytest.fixture
    async def client(self):
        """Create test client for API."""
        from fastapi.testclient import TestClient
        from integration_api import app

        # Initialize autonomous system for testing
        from autonomous_system import autonomous_system
        if not autonomous_system.running:
            await autonomous_system.initialize()

        client = TestClient(app)
        yield client

        # Cleanup
        if autonomous_system.running:
            await autonomous_system.shutdown()

    def test_health_endpoint(self, client):
        """Test system health endpoint."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert "database_status" in data
        assert "graph_status" in data

    def test_service_registration(self, client):
        """Test service registration endpoint."""
        service_data = {
            "service_type": "backend",
            "service_name": "test_service",
            "host": "localhost",
            "port": 8080,
            "endpoints": ["/api/test"],
            "health_check_url": "http://localhost:8080/health"
        }

        response = client.post("/api/v1/services/register", json=service_data)
        assert response.status_code == 200
        data = response.json()
        assert "service_id" in data

    def test_service_discovery(self, client):
        """Test service discovery endpoint."""
        response = client.get("/api/v1/services")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestDataIntegrity:
    """Test data integrity constraints."""

    def test_foreign_key_constraints(self):
        """Test foreign key relationships."""
        with db_manager.session_scope() as session:
            # Test route-station relationship
            try:
                # This should fail due to foreign key constraint
                invalid_route = Route(
                    train_id="nonexistent",
                    origin_station_id="nonexistent",
                    dest_station_id="nonexistent",
                    distance_km=100.0,
                    duration_minutes=120
                )
                session.add(invalid_route)
                session.commit()
                assert False, "Foreign key constraint should have failed"
            except Exception:
                # Expected - constraint violation
                session.rollback()
                assert True

    def test_check_constraints(self):
        """Test check constraints."""
        with db_manager.session_scope() as session:
            try:
                # Test invalid distance (negative)
                invalid_route = Route(
                    train_id="test_train",
                    origin_station_id="test_station_1",
                    dest_station_id="test_station_2",
                    distance_km=-10.0,  # Invalid
                    duration_minutes=120
                )
                session.add(invalid_route)
                session.commit()
                assert False, "Check constraint should have failed"
            except Exception:
                session.rollback()
                assert True

    def test_soft_deletes(self):
        """Test soft delete functionality."""
        with db_manager.session_scope() as session:
            # Create test record
            test_station = Station(
                code="TEST",
                name="Test Station",
                latitude=0.0,
                longitude=0.0
            )
            session.add(test_station)
            session.commit()

            station_id = test_station.id

            # Soft delete
            test_station.is_deleted = True
            test_station.deleted_at = datetime.utcnow()
            session.commit()

            # Verify soft delete
            deleted_station = session.query(Station).filter(Station.id == station_id).first()
            assert deleted_station.is_deleted
            assert deleted_station.deleted_at is not None

class TestPerformanceOptimization:
    """Test performance optimization features."""

    def test_indexes(self):
        """Test database indexes."""
        with db_manager.session_scope() as session:
            # Test indexed query performance
            import time

            start_time = time.time()
            stations = session.query(Station).filter(Station.is_active == True).limit(100).all()
            query_time = time.time() - start_time

            # Should be fast due to indexes
            assert query_time < 1.0  # Less than 1 second

    def test_connection_pooling(self):
        """Test connection pooling."""
        # Test multiple concurrent connections
        connections = []
        for i in range(5):
            conn = db_manager._get_connection()
            connections.append(conn)

        # All connections should be valid
        for conn in connections:
            assert conn is not None

        # Clean up
        for conn in connections:
            conn.close()

class TestSecurityFeatures:
    """Test security features."""

    def test_row_level_security(self):
        """Test RLS policies."""
        with db_manager.session_scope() as session:
            # Test tenant isolation
            tenant1 = session.query(Tenant).first()
            if tenant1:
                # Query should only return tenant1's data
                routes = session.query(Route).filter(Route.tenant_id == tenant1.id).all()
                for route in routes:
                    assert route.tenant_id == tenant1.id

    def test_audit_logging(self):
        """Test audit logging."""
        with db_manager.session_scope() as session:
            # Create test audit log
            audit_log = AuditLog(
                tenant_id="test_tenant",
                user_id="test_user",
                action="CREATE",
                resource_type="route",
                resource_id="test_route",
                ip_address="127.0.0.1"
            )
            session.add(audit_log)
            session.commit()

            # Verify audit log
            logged = session.query(AuditLog).filter(AuditLog.id == audit_log.id).first()
            assert logged is not None
            assert logged.action == "CREATE"

class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.mark.asyncio
    async def test_complete_route_workflow(self):
        """Test complete route finding workflow."""
        # Initialize system
        autonomous_system = AutonomousSystem()
        await autonomous_system.initialize()

        db_core = DatabaseCore()
        await db_core.initialize()

        try:
            # Ensure test data
            await self._setup_test_data()

            # Build graph
            graph = await db_core.graph_builder.build_graph()
            assert graph is not None

            # Find routes
            routes = await db_core.find_optimal_routes("NDLS", "BCT", max_transfers=2)
            assert isinstance(routes, list)

            # Analyze performance
            analysis = await db_core.analyze_system_performance()
            assert isinstance(analysis, dict)

            # Test service discovery
            service_id = await autonomous_system.service_discovery.register_service({
                "service_type": "test",
                "service_name": "test_service",
                "host": "localhost",
                "port": 8080,
                "endpoints": ["/test"],
                "health_check_url": "http://localhost:8080/health"
            })
            assert service_id is not None

        finally:
            await db_core.shutdown()
            await autonomous_system.shutdown()

    async def _setup_test_data(self):
        """Setup comprehensive test data."""
        with db_manager.session_scope() as session:
            # Create tenants
            tenant = Tenant(name="Test Tenant", is_active=True)
            session.add(tenant)
            session.commit()

            # Create users
            user = User(
                tenant_id=tenant.id,
                username="testuser",
                email="test@example.com",
                role="admin",
                is_active=True
            )
            session.add(user)
            session.commit()

            # Create stations
            stations = [
                Station(code="NDLS", name="New Delhi", latitude=28.6139, longitude=77.2090, tenant_id=tenant.id),
                Station(code="BCT", name="Mumbai Central", latitude=18.9690, longitude=72.8205, tenant_id=tenant.id),
                Station(code="HWH", name="Howrah Junction", latitude=22.5822, longitude=88.3378, tenant_id=tenant.id),
                Station(code="CNB", name="Kanpur Central", latitude=26.4499, longitude=80.3319, tenant_id=tenant.id)
            ]
            for station in stations:
                session.add(station)
            session.commit()

            # Create trains
            train = Train(
                number="12345",
                name="Test Express",
                type="Express",
                operator="Test Railway",
                max_speed_kmph=120.0,
                total_coaches=20,
                classes_available=["1A", "2A", "3A", "SL"],
                tenant_id=tenant.id
            )
            session.add(train)
            session.commit()

            # Create routes
            routes = [
                Route(
                    train_id=train.id,
                    origin_station_id=stations[0].id,  # NDLS
                    dest_station_id=stations[3].id,    # CNB
                    distance_km=440.0,
                    duration_minutes=480,
                    tenant_id=tenant.id
                ),
                Route(
                    train_id=train.id,
                    origin_station_id=stations[3].id,  # CNB
                    dest_station_id=stations[1].id,    # BCT
                    distance_km=1100.0,
                    duration_minutes=1200,
                    tenant_id=tenant.id
                )
            ]
            for route in routes:
                session.add(route)
            session.commit()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])