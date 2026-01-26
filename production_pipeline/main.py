"""
Main Application Entry Point

Initializes and runs the complete production pipeline system.
"""

import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from production_pipeline.config import get_config, create_directories
from production_pipeline.database import DatabaseManager
from production_pipeline.ingestion import AsyncHTTPClient, IngestionOrchestrator, CacheManager
from production_pipeline.routing_engine import RoutingEngine
from production_pipeline.jobs import JobScheduler
from production_pipeline.observability import initialize_observability
from production_pipeline.api import create_app

# Configure logging
logger = logging.getLogger(__name__)


class ProductionPipeline:
    """Main production pipeline application"""
    
    def __init__(self):
        """Initialize production pipeline"""
        logger.info("Initializing Production Pipeline...")
        
        self.config = get_config()
        
        # Initialize observability first
        initialize_observability()
        
        # Create required directories
        create_directories()
        
        # Initialize database
        logger.info(f"Using database: {self.config.database.connection_string}")
        self.db_manager = DatabaseManager(
            self.config.database.connection_string,
            echo_sql=self.config.environment.name == "LOCAL"
        )
        
        # Initialize cache
        self.cache_manager = CacheManager(
            Path(self.config.cache.cache_dir),
            ttl_seconds=self.config.ingestion.cache_ttl_seconds
        )
        
        # Initialize HTTP client
        self.http_client = None
        
        # Initialize routing engine
        session = self.db_manager.get_session()
        self.routing_engine = RoutingEngine(session)
        session.close()
        
        # Initialize ingestion orchestrator
        self.ingestion_orchestrator = None
        
        # Initialize job scheduler
        self.job_scheduler = JobScheduler(self.db_manager, self.ingestion_orchestrator)
        
        # Initialize FastAPI app
        self.app = create_app(self.db_manager, self.routing_engine, self.cache_manager)
        
        logger.info("Production Pipeline initialized successfully")
    
    async def start(self):
        """Start the production pipeline
        
        This starts:
        - Database connections
        - HTTP client for ingestion
        - Job scheduler
        - FastAPI server
        """
        logger.info("Starting Production Pipeline...")
        
        try:
            # Create database tables if needed
            self.db_manager.create_all_tables()
            logger.info("Database tables created")
            
            # Start HTTP client
            self.http_client = AsyncHTTPClient(self.cache_manager)
            await self.http_client.start()
            logger.info("HTTP client started")
            
            # Initialize ingestion orchestrator
            self.ingestion_orchestrator = IngestionOrchestrator(self.http_client)
            
            # Schedule background jobs
            self.job_scheduler.schedule_jobs()
            self.job_scheduler.start()
            logger.info("Job scheduler started")
            
            logger.info("Production Pipeline started successfully")
            logger.info(f"API available at: http://localhost:{self.config.api.port}")
            logger.info(f"Health check: http://localhost:{self.config.api.port}/api/v1/health")
            
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}", exc_info=True)
            raise
    
    async def shutdown(self):
        """Shutdown the production pipeline"""
        logger.info("Shutting down Production Pipeline...")
        
        try:
            # Stop job scheduler
            if self.job_scheduler:
                self.job_scheduler.shutdown()
                logger.info("Job scheduler stopped")
            
            # Close HTTP client
            if self.http_client:
                await self.http_client.close()
                logger.info("HTTP client closed")
            
            # Close database
            if self.db_manager:
                self.db_manager.close()
                logger.info("Database closed")
            
            logger.info("Production Pipeline shutdown complete")
        
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    async def run_server(self):
        """Run the production pipeline with server"""
        import uvicorn
        
        await self.start()
        
        try:
            config = uvicorn.Config(
                self.app,
                host=self.config.api.host,
                port=self.config.api.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        
        finally:
            await self.shutdown()


# FastAPI lifespan context manager
@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan events
    
    Handles startup and shutdown of the application.
    """
    # Startup
    pipeline = app.state.pipeline
    await pipeline.start()
    
    yield
    
    # Shutdown
    await pipeline.shutdown()


def create_pipeline_app():
    """Create FastAPI app with production pipeline integration
    
    Returns:
        FastAPI application with pipeline attached
    """
    # Create pipeline instance
    pipeline = ProductionPipeline()
    
    # Get the FastAPI app and add pipeline state
    app = pipeline.app
    app.state.pipeline = pipeline
    
    # Add lifespan
    # Note: For FastAPI, the app creation happens before lifespan can be assigned
    # We'll initialize everything in main startup
    
    return app, pipeline


async def main():
    """Main entry point"""
    # Create pipeline
    pipeline = ProductionPipeline()
    
    # Run server
    await pipeline.run_server()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
