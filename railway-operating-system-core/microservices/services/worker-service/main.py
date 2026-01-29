# ===============================================
# WORKER SERVICE
# ===============================================
# Asynchronous job processing service using Celery
# Handles long-running route searches and background tasks

import os
import sys
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Add project root to path to enable shared module imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from celery import Celery
from celery.signals import worker_ready, worker_shutdown
import httpx

from shared.models import DatabaseManager
from shared.route_finder_engine import RouteFinderEngine
from shared.config import (
    DATABASE_CONFIG, REDIS_CONFIG, RABBITMQ_CONFIG,
    ROUTE_CONFIG, JOB_CONFIG
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'railway_worker',
    broker=RABBITMQ_CONFIG['url'],
    backend=REDIS_CONFIG['url'],
    include=['main']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'main.process_route_search': {'queue': 'route_jobs'},
    },
    task_default_queue='route_jobs',
    task_default_exchange='railway_os',
    task_default_routing_key='route_jobs',
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
)

# Global components
db_manager = None
route_engine = RouteFinderEngine()
http_client = None

# ===============================================
# CELERY TASKS
# ===============================================

@celery_app.task(bind=True, max_retries=JOB_CONFIG['max_retries'])
def process_route_search(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process asynchronous route search job"""
    try:
        job_id = job_data['job_id']
        tenant_id = job_data['tenant_id']
        request_data = job_data['request']

        logger.info(f"Processing route search job {job_id} for tenant {tenant_id}")

        # Update job status to processing
        update_job_status(job_id, 'processing')

        # Get route data from data service
        route_data = get_route_data_from_data_service(tenant_id, request_data)

        # Prepare data for route engine
        stations_data = route_data['stations']
        train_schedule_data = route_data['train_schedule']

        # Convert running days to dict format
        train_running_days = {}
        for rd in route_data['train_running_days']:
            train_running_days[rd['train_no']] = {
                'mon': rd['mon'],
                'tue': rd['tue'],
                'wed': rd['wed'],
                'thu': rd['thu'],
                'fri': rd['fri'],
                'sat': rd['sat'],
                'sun': rd['sun']
            }

        # Perform route search
        result = route_engine.find_routes(
            source=request_data['source'],
            destination=request_data['destination'],
            date=datetime.fromisoformat(request_data['date']).date(),
            train_schedule_data=train_schedule_data,
            train_running_days=train_running_days,
            stations_data=stations_data,
            max_transfers=request_data.get('max_transfers', ROUTE_CONFIG['max_transfers'])
        )

        # Store result in Redis
        redis_client = celery_app.backend.client
        redis_client.setex(f"job_result:{job_id}", 3600, json.dumps(result))  # 1 hour TTL

        # Update job status to completed
        update_job_status(job_id, 'completed')

        logger.info(f"Route search job {job_id} completed successfully")
        return result

    except Exception as e:
        logger.error(f"Route search job {job_data.get('job_id', 'unknown')} failed: {e}")

        # Update job status to failed
        job_id = job_data.get('job_id')
        if job_id:
            update_job_status(job_id, 'failed', str(e))

        # Retry with exponential backoff
        raise self.retry(countdown=2 ** self.request.retries, exc=e)

# ===============================================
# UTILITY FUNCTIONS
# ===============================================

def update_job_status(job_id: str, status: str, error_message: Optional[str] = None):
    """Update job status in database"""
    try:
        session = db_manager.get_session()

        update_data = {
            'status': status,
            'completed_at': datetime.utcnow() if status in ['completed', 'failed'] else None,
        }

        if status == 'processing':
            update_data['started_at'] = datetime.utcnow()
        elif status == 'failed' and error_message:
            update_data['error_message'] = error_message

        # Build dynamic update query
        set_clause = ', '.join(f"{k} = %s" for k in update_data.keys())
        values = list(update_data.values()) + [job_id]

        session.execute(f"""
            UPDATE job_queue
            SET {set_clause}
            WHERE job_id = %s
        """, values)

        session.commit()
        session.close()

    except Exception as e:
        logger.error(f"Failed to update job status: {e}")

def get_route_data_from_data_service(tenant_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch route data from data service"""
    try:
        data_service_url = os.getenv('DATA_SERVICE_URL', 'http://data-service:8003')
        url = f"{data_service_url}/v1/route-data"

        # Synchronous HTTP call (since we're in a worker)
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                url,
                params={'tenant_id': tenant_id}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch route data: {e}")
        raise

# ===============================================
# CELERY SIGNALS
# ===============================================

@worker_ready.connect
def worker_ready_handler(sender, **kwargs):
    """Handle worker startup"""
    global db_manager, http_client

    try:
        logger.info("Initializing Railway Worker Service...")

        # Initialize database connection
        db_manager = DatabaseManager(DATABASE_CONFIG['url'])
        if not db_manager.connect():
            raise Exception("Failed to connect to database")

        # Initialize HTTP client
        http_client = httpx.Client(timeout=30.0)

        logger.info("Railway Worker Service initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize worker: {e}")
        raise

@worker_shutdown.connect
def worker_shutdown_handler(sender, **kwargs):
    """Handle worker shutdown"""
    global db_manager, http_client

    try:
        if http_client:
            http_client.close()
        if db_manager:
            db_manager.disconnect()
        logger.info("Railway Worker Service shut down successfully")
    except Exception as e:
        logger.error(f"Error during worker shutdown: {e}")

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == '__main__':
    # Start Celery worker
    celery_app.start()