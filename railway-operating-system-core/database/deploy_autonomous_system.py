# deploy_autonomous_system.py - Autonomous System Deployment
"""
Deployment script for the autonomous railway operating system.
Handles complete setup, configuration, and startup of all components.
"""

import asyncio
import os
import sys
import subprocess
import logging
from pathlib import Path
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutonomousSystemDeployer:
    """Handles deployment of the autonomous railway operating system."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.database_path = self.base_path / "database"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load deployment configuration."""
        config_path = self.database_path / "deployment_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "name": "railway_os",
                    "user": "railway_user",
                    "password": "secure_password_123"
                },
                "api": {
                    "host": "0.0.0.0",
                    "port": 8001,
                    "workers": 4
                },
                "monitoring": {
                    "enabled": True,
                    "metrics_port": 9090
                },
                "security": {
                    "jwt_secret": "your-super-secret-jwt-key-change-in-production",
                    "encryption_key": "your-encryption-key-32-chars-long"
                },
                "autonomous": {
                    "optimization_interval": 300,  # 5 minutes
                    "health_check_interval": 60,   # 1 minute
                    "schema_sync_interval": 3600   # 1 hour
                }
            }

    async def deploy(self):
        """Execute complete deployment."""
        logger.info("Starting autonomous system deployment...")

        try:
            # Step 1: Environment setup
            await self._setup_environment()

            # Step 2: Database initialization
            await self._initialize_database()

            # Step 3: Install dependencies
            await self._install_dependencies()

            # Step 4: Run database migrations
            await self._run_migrations()

            # Step 5: Seed initial data
            await self._seed_data()

            # Step 6: Start autonomous system
            await self._start_autonomous_system()

            # Step 7: Start API server
            await self._start_api_server()

            # Step 8: Health checks
            await self._run_health_checks()

            logger.info("Deployment completed successfully!")

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            await self._rollback()
            raise

    async def _setup_environment(self):
        """Setup deployment environment."""
        logger.info("Setting up environment...")

        # Create necessary directories
        directories = [
            self.database_path / "logs",
            self.database_path / "backups",
            self.database_path / "cache",
            self.database_path / "temp"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

        # Set environment variables
        os.environ.update({
            "DATABASE_URL": f"postgresql://{self.config['database']['user']}:{self.config['database']['password']}@{self.config['database']['host']}:{self.config['database']['port']}/{self.config['database']['name']}",
            "JWT_SECRET": self.config['security']['jwt_secret'],
            "ENCRYPTION_KEY": self.config['security']['encryption_key'],
            "PYTHONPATH": str(self.database_path)
        })

        logger.info("Environment setup completed")

    async def _initialize_database(self):
        """Initialize PostgreSQL database."""
        logger.info("Initializing database...")

        # Check if PostgreSQL is running
        try:
            result = subprocess.run(
                ["pg_isready", "-h", self.config['database']['host'], "-p", str(self.config['database']['port'])],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise Exception("PostgreSQL is not running")
        except FileNotFoundError:
            logger.warning("pg_isready not found, assuming PostgreSQL is running")

        # Create database and user if they don't exist
        create_db_script = f"""
        -- Create user and database
        DO $$
        BEGIN
           IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{self.config['database']['user']}') THEN
              CREATE ROLE {self.config['database']['user']} LOGIN PASSWORD '{self.config['database']['password']}';
           END IF;
        END
        $$;

        -- Create database if it doesn't exist
        SELECT 'CREATE DATABASE {self.config['database']['name']} OWNER {self.config['database']['user']}'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '{self.config['database']['name']}')\\gexec
        """

        with open(self.database_path / "create_db.sql", 'w') as f:
            f.write(create_db_script)

        # Execute database creation
        try:
            subprocess.run([
                "psql", "-h", self.config['database']['host'],
                "-p", str(self.config['database']['port']),
                "-U", "postgres", "-f", str(self.database_path / "create_db.sql")
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Database creation might have failed: {e}")

        logger.info("Database initialization completed")

    async def _install_dependencies(self):
        """Install Python dependencies."""
        logger.info("Installing dependencies...")

        requirements_file = self.database_path / "requirements.txt"
        if not requirements_file.exists():
            # Create requirements file
            requirements = [
                "fastapi==0.104.1",
                "uvicorn[standard]==0.24.0",
                "sqlalchemy==2.0.23",
                "psycopg2-binary==2.9.9",
                "alembic==1.12.1",
                "networkx==3.1",
                "pydantic==2.5.0",
                "python-multipart==0.0.6",
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4",
                "psutil==5.9.6",
                "aiofiles==23.2.1",
                "httpx==0.25.2",
                "pytest==7.4.3",
                "pytest-asyncio==0.21.1",
                "cryptography==41.0.7",
                "redis==5.0.1",
                "celery==5.3.4"
            ]

            with open(requirements_file, 'w') as f:
                f.write('\n'.join(requirements))

        # Install dependencies
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, cwd=self.database_path)

        logger.info("Dependencies installation completed")

    async def _run_migrations(self):
        """Run database migrations."""
        logger.info("Running database migrations...")

        # Initialize Alembic if not already done
        alembic_dir = self.database_path / "alembic"
        if not alembic_dir.exists():
            subprocess.run([
                "alembic", "init", "alembic"
            ], cwd=self.database_path, check=True)

            # Configure alembic
            alembic_ini = self.database_path / "alembic.ini"
            with open(alembic_ini, 'r') as f:
                content = f.read()

            content = content.replace(
                "sqlalchemy.url = driver://user:pass@localhost/dbname",
                f"sqlalchemy.url = postgresql://{self.config['database']['user']}:{self.config['database']['password']}@{self.config['database']['host']}:{self.config['database']['port']}/{self.config['database']['name']}"
            )

            with open(alembic_ini, 'w') as f:
                f.write(content)

        # Generate and run migrations
        subprocess.run([
            "alembic", "revision", "--autogenerate", "-m", "Initial migration"
        ], cwd=self.database_path, check=True)

        subprocess.run([
            "alembic", "upgrade", "head"
        ], cwd=self.database_path, check=True)

        logger.info("Database migrations completed")

    async def _seed_data(self):
        """Seed initial data."""
        logger.info("Seeding initial data...")

        # Import and run data seeding
        sys.path.insert(0, str(self.database_path))

        from database_core import db_core

        await db_core.initialize()
        await db_core.seed_initial_data()
        await db_core.shutdown()

        logger.info("Data seeding completed")

    async def _start_autonomous_system(self):
        """Start the autonomous system."""
        logger.info("Starting autonomous system...")

        from autonomous_system import autonomous_system

        # Initialize and start autonomous system
        await autonomous_system.initialize()

        # Start background tasks
        asyncio.create_task(autonomous_system.run_background_tasks())

        logger.info("Autonomous system started")

    async def _start_api_server(self):
        """Start the API server."""
        logger.info("Starting API server...")

        from integration_api import app
        import uvicorn

        # Start API server in background
        config = uvicorn.Config(
            app,
            host=self.config['api']['host'],
            port=self.config['api']['port'],
            workers=self.config['api']['workers'],
            log_level="info"
        )
        server = uvicorn.Server(config)

        # Run server in background
        asyncio.create_task(server.serve())

        logger.info(f"API server started on {self.config['api']['host']}:{self.config['api']['port']}")

    async def _run_health_checks(self):
        """Run comprehensive health checks."""
        logger.info("Running health checks...")

        import httpx
        import time

        # Wait for services to start
        await asyncio.sleep(5)

        # Check API health
        api_url = f"http://{self.config['api']['host']}:{self.config['api']['port']}/api/v1/system/health"
        max_retries = 10
        retry_count = 0

        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(api_url)
                    if response.status_code == 200:
                        health_data = response.json()
                        logger.info(f"API health check passed: {health_data}")
                        break
                    else:
                        logger.warning(f"API health check failed with status {response.status_code}")
            except Exception as e:
                logger.warning(f"API health check failed: {e}")

            retry_count += 1
            await asyncio.sleep(2)

        if retry_count >= max_retries:
            raise Exception("API health check failed after maximum retries")

        # Check autonomous system
        from autonomous_system import autonomous_system
        system_status = await autonomous_system.get_system_status()
        logger.info(f"Autonomous system status: {system_status}")

        logger.info("Health checks completed successfully")

    async def _rollback(self):
        """Rollback deployment in case of failure."""
        logger.info("Rolling back deployment...")

        # Stop any running processes
        try:
            from autonomous_system import autonomous_system
            if autonomous_system.running:
                await autonomous_system.shutdown()
        except:
            pass

        # Clean up created files/directories if needed
        # Note: In production, you might want to be more careful about cleanup

        logger.info("Rollback completed")

async def main():
    """Main deployment function."""
    if len(sys.argv) != 2:
        print("Usage: python deploy_autonomous_system.py <base_path>")
        sys.exit(1)

    base_path = sys.argv[1]

    deployer = AutonomousSystemDeployer(base_path)
    await deployer.deploy()

if __name__ == "__main__":
    asyncio.run(main())