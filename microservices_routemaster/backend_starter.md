# Backend System Starter and Requirements

## Overview
The Backend System is a FastAPI-based microservice providing REST APIs for the Railway Operating System. It includes JWT-based authentication, role-based access control (RBAC), resilience patterns, observability, and API versioning.

## Requirements

### System Requirements
- Python 3.10+ (3.11 recommended)
- PostgreSQL 14+ (for production database)
- Redis 6+ (for caching and job queue)
- pip or poetry for dependency management

### Dependencies
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
celery==5.3.4
prometheus-client==0.19.0
opentelemetry-distro==0.43b0
opentelemetry-instrumentation-fastapi==0.43b0
structlog==23.2.0
httpx==0.25.2
tenacity==8.2.3
```

## Techniques Used

### API Framework
- **FastAPI**: High-performance async web framework
- **Pydantic**: Data validation and serialization
- **Semantic Versioning**: API versioning with /v1 prefix

### Authentication & Authorization
- **JWT Tokens**: JSON Web Tokens for stateless authentication
- **RBAC**: 5 roles (admin, developer, operator, user, guest) with granular permissions
- **API Key Authentication**: Tenant-based API keys for multi-tenancy

### Resilience Patterns
- **Circuit Breaker**: Prevents cascading failures
- **Bulkhead**: Isolates resource usage
- **Retry Logic**: Exponential backoff for transient failures
- **Rate Limiting**: Token bucket algorithm (100 RPS per tenant)

### Observability
- **Prometheus Metrics**: Application and system metrics
- **OpenTelemetry Tracing**: Distributed tracing across services
- **Structured Logging**: JSON logs with correlation IDs
- **Health Checks**: Readiness and liveness probes

### Data Management
- **SQLAlchemy ORM**: Object-relational mapping
- **Alembic Migrations**: Database schema versioning
- **Connection Pooling**: Efficient database connections
- **Caching**: Redis-based caching with TTL

### Asynchronous Processing
- **Celery Workers**: Background job processing
- **Redis Broker**: Message queue for job distribution

## Data Requirements

### Database Schema
The backend requires a PostgreSQL database with the following tables:

#### Core Tables
```sql
-- Tenants
CREATE TABLE tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Routes
CREATE TABLE routes (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    origin_station VARCHAR(100) NOT NULL,
    dest_station VARCHAR(100) NOT NULL,
    distance_km DECIMAL(10,2),
    duration_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Stations
CREATE TABLE stations (
    id UUID PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Jobs
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    payload JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### External Data Sources
- **Railway Datasets**: CSV files for stations, trains, schedules
- **ETL Pipeline**: Automated data ingestion and transformation
- **Backup Storage**: S3-compatible storage for database dumps

### Configuration Data
```python
# config.py
class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/railway_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # JWT
    jwt_secret: str = "your-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_version: str = "/v1"
    
    # Security
    cors_origins: list = ["http://localhost:3000"]
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Observability
    prometheus_port: int = 9090
    log_level: str = "INFO"
```

## Setup and Installation

### 1. Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Install PostgreSQL and create database
createdb railway_db

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_database.py
```

### 3. Redis Setup
```bash
# Install Redis
# On Ubuntu: sudo apt install redis-server
# On macOS: brew install redis
# Start Redis server
redis-server
```

### 4. Environment Configuration
Create `.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/railway_db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-super-secret-jwt-key-here
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Start the Application
```bash
# Start API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# In production
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Start Workers (Optional)
```bash
# Start Celery workers
celery -A workers.celery_app worker --loglevel=info
```

### 7. Testing
```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app --cov-report=html

# Run integration tests (requires database)
pytest tests/integration/
```

## API Endpoints

### Authentication
- `POST /v1/auth/login` - User authentication
- `POST /v1/auth/refresh` - Token refresh
- `GET /v1/auth/me` - Current user info

### Routes
- `GET /v1/routes/search` - Search routes with filters
- `GET /v1/routes/{id}` - Get route details
- `POST /v1/routes` - Create new route (admin)
- `PUT /v1/routes/{id}` - Update route (admin)
- `DELETE /v1/routes/{id}` - Delete route (admin)

### Stations
- `GET /v1/stations` - List all stations
- `GET /v1/stations/{id}` - Get station details
- `POST /v1/stations` - Create station (admin)

### Jobs
- `GET /v1/jobs` - List user jobs
- `GET /v1/jobs/{id}` - Get job status and result
- `POST /v1/jobs` - Submit new job
- `DELETE /v1/jobs/{id}` - Cancel job

### Admin
- `GET /v1/admin/tenants` - List tenants (super admin)
- `GET /v1/admin/metrics` - System metrics
- `GET /v1/admin/health` - Health check

## Integration Points

### With Frontend
- REST API communication
- JWT token handling
- CORS configuration for cross-origin requests

### With Database
- Direct SQLAlchemy connection
- Alembic migrations for schema changes
- Connection pooling and transaction management

### With Deployment
- Environment-based configuration
- Health check endpoints for load balancers
- Graceful shutdown handling

## Development Workflow

1. **API Development**: Use FastAPI decorators for endpoint definition
2. **Data Models**: Define Pydantic models for request/response validation
3. **Authentication**: Use dependency injection for user context
4. **Database**: Use SQLAlchemy sessions with proper transaction handling
5. **Testing**: Write unit tests for business logic, integration tests for APIs
6. **Logging**: Use structured logging with correlation IDs

## Key Files Structure
```
backend_system/
├── main.py                 # FastAPI application
├── config.py              # Settings and configuration
├── database.py            # Database connection and session
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── route.py
│   └── job.py
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   ├── auth.py
│   └── route.py
├── api/                   # API endpoints
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── routes.py
│   │   └── jobs.py
│   └── dependencies.py
├── core/                  # Core functionality
│   ├── auth.py           # JWT and RBAC
│   ├── security.py       # Password hashing
│   └── cache.py          # Redis caching
├── services/             # Business logic
│   ├── route_service.py
│   └── job_service.py
├── workers/              # Celery workers
│   ├── __init__.py
│   └── tasks.py
├── tests/                # Test files
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_routes.py
├── alembic/              # Database migrations
├── requirements.txt
└── Dockerfile
```</content>
<parameter name="filePath">c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\railway-operating-system-microservices\backend_starter.md