# Railway Operating System Backend

A FastAPI-based microservice providing REST APIs for the Railway Operating System with JWT authentication, RBAC, and multi-tenancy support.

## Features

- **FastAPI Framework**: High-performance async web framework
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control**: 5-tier role system (guest, user, operator, developer, admin)
- **Multi-tenancy**: Tenant-based data isolation
- **PostgreSQL Database**: Robust data persistence with SQLAlchemy ORM
- **Redis Caching**: High-performance caching layer
- **Celery Workers**: Asynchronous job processing
- **Prometheus Metrics**: Application monitoring and observability
- **Structured Logging**: JSON logs with correlation IDs
- **API Versioning**: Semantic versioning with /v1 prefix

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### Installation

1. **Clone and setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment configuration:**
   ```bash
   cp .env.example .env
   # Edit .env with your database and Redis credentials
   ```

3. **Database setup:**
   ```bash
   # Create database
   createdb railway_db

   # Run migrations
   cd ../database
   alembic upgrade head
   ```

4. **Start services:**
   ```bash
   # Start Redis
   redis-server

   # Start API server
   cd ../backend
   python main.py

   # Start workers (in another terminal)
   celery -A workers.tasks.celery_app worker --loglevel=info
   ```

### API Endpoints

#### Authentication
- `POST /v1/auth/login` - User login
- `POST /v1/auth/refresh` - Refresh token
- `GET /v1/auth/me` - Current user info

#### Routes
- `GET /v1/routes/search` - Search routes
- `GET /v1/routes/{id}` - Get route details
- `POST /v1/routes` - Create route (operator+)
- `PUT /v1/routes/{id}` - Update route (operator+)
- `DELETE /v1/routes/{id}` - Delete route (operator+)

#### Stations
- `GET /v1/stations` - List stations
- `GET /v1/stations/{id}` - Get station details
- `POST /v1/stations` - Create station (operator+)

#### Jobs
- `GET /v1/jobs` - List user jobs
- `GET /v1/jobs/{id}` - Get job status
- `POST /v1/jobs` - Submit job
- `DELETE /v1/jobs/{id}` - Cancel job

### Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=app --cov-report=html

# Run integration tests
pytest tests/integration/
```

### Docker Deployment

```bash
# Build image
docker build -t railway-backend .

# Run container
docker run -p 8000:8000 --env-file .env railway-backend
```

## Architecture

```
backend/
├── main.py                 # FastAPI application
├── config.py              # Settings and configuration
├── database.py            # Database connection
├── models/                # SQLAlchemy models
├── schemas/               # Pydantic schemas
├── api/v1/               # API endpoints
├── core/                  # Core functionality
│   ├── auth.py           # Authentication & RBAC
│   ├── security.py       # Password hashing
│   └── cache.py          # Redis caching
├── services/             # Business logic
├── workers/              # Celery workers
├── tests/                # Test files
├── alembic/              # Database migrations
├── requirements.txt
└── Dockerfile
```

## Security

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- CORS protection
- Rate limiting (100 RPS per tenant)
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy

## Monitoring

- **Health Checks**: `/health` and `/ready` endpoints
- **Metrics**: `/metrics` endpoint with Prometheus format
- **Logging**: Structured JSON logs with correlation IDs
- **Tracing**: OpenTelemetry integration ready

## Development

### Code Style

Follow PEP 8 standards and use type hints throughout the codebase.

### API Documentation

- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```