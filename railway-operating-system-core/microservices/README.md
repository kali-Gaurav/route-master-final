# Railway Operating System - Microservices Platform

A comprehensive, multi-tenant SaaS platform for railway route finding and operations management. Built as a microservices architecture with API-first design, supporting multiple railway companies with isolated data and scalable processing.

## 🏗️ Architecture Overview

The platform consists of the following microservices:

- **API Gateway**: Single entry point with authentication, rate limiting, and request routing
- **Auth Service**: Tenant management and API key validation
- **Route Service**: Route finding engine with caching and optimization
- **Data Service**: Database access layer with multi-tenant isolation
- **Worker Service**: Asynchronous job processing with Celery and RabbitMQ

### Infrastructure Components
- **PostgreSQL**: Multi-tenant database with schema-per-tenant isolation
- **Redis**: Caching and session storage
- **RabbitMQ**: Message queuing for async processing
- **Nginx**: Reverse proxy and load balancing (production)

### Core Services Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │────│   Auth Service  │────│  Data Service   │
│   (Port 8000)   │    │   (Port 8001)   │    │  (Port 8003)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Route Service  │────│ Worker Service  │
                    │  (Port 8002)   │    │  (Port 8004)    │
                    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.8+ (for development)
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd railway-operating-system-microservices
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

### 3. Start the Platform
```bash
# Using the setup script (recommended)
./setup.sh start

# Or manually with Docker Compose
docker-compose up -d
```

### 4. Verify Installation
```bash
# Run comprehensive tests
./test-system.sh

# Check service health
curl http://localhost:8000/health
```

### 5. Create Your First Tenant
```python
from sdk.python.railway_os_sdk import RailwayOSClient

# The platform creates a default tenant for testing
# Use the test credentials from the logs or create a new tenant
client = RailwayOSClient(
    api_key="test-api-key-from-logs",
    tenant_id="test-tenant-from-logs"
)

# Search for routes
routes = client.search_routes("Delhi", "Mumbai", "2024-01-15")
print(f"Found {len(routes['routes'])} routes")
```

## 📋 API Documentation

### OpenAPI Specification
- **Development**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc

### Core Endpoints

#### Health Checks
```bash
# All services
GET /health

# Specific service
GET /health/api-gateway
```

#### Route Search
```bash
# Synchronous search
POST /api/v1/routes/search
{
  "origin": "Delhi",
  "destination": "Mumbai",
  "date": "2024-01-15",
  "max_transfers": 3
}

# Asynchronous search
POST /api/v1/routes/search-async
# Returns job_id for status tracking
```

#### Tenant Management
```bash
# Create tenant
POST /api/v1/tenants

# Get tenant info
GET /api/v1/tenants/{tenant_id}

# Update tenant
PUT /api/v1/tenants/{tenant_id}
```

#### Data Access
```bash
# List stations
GET /api/v1/stations?search=Delhi&limit=10

# Get station details
GET /api/v1/stations/{station_id}

# List trains
GET /api/v1/trains?search=Rajdhani
```

## 🛠️ Development

### Project Structure
```
railway-operating-system-microservices/
├── docker/                          # Docker configurations
│   ├── init-db.sql                 # Database initialization
│   └── ...
├── services/                       # Microservices
│   ├── api-gateway/                # API Gateway service
│   ├── auth-service/               # Authentication service
│   ├── route-service/               # Route finding service
│   ├── data-service/               # Data access service
│   └── worker-service/             # Async worker service
├── shared/                         # Shared libraries
│   ├── config.py                   # Configuration management
│   ├── models.py                   # Database models
│   └── route_finder_engine.py      # Route finding logic
├── sdk/                           # Client SDKs
│   └── python/                     # Python SDK
├── docker-compose.yml              # Development orchestration
├── docker-compose.prod.yml         # Production deployment
├── setup.sh                        # Setup script
├── setup.bat                       # Windows setup script
├── test-system.sh                  # Testing script
└── README.md                       # This file
```

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements-dev.txt

# Start infrastructure only
docker-compose up -d postgres redis rabbitmq

# Run a specific service locally
cd services/api-gateway
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Running Tests
```bash
# All services
./test-system.sh

# Specific service
cd services/route-service
python -m pytest tests/

# With coverage
python -m pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black services/ shared/ sdk/

# Lint code
flake8 services/ shared/ sdk/

# Type checking
mypy services/ shared/ sdk/
```

## 🚢 Deployment

### Development Deployment
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale route-service=3
```

### Production Deployment
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# With environment file
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Production Features
- **Load Balancing**: Nginx reverse proxy with sticky sessions
- **Resource Limits**: CPU and memory limits per service
- **Health Checks**: Automatic service restart on failure
- **Scaling**: Horizontal scaling with replica management
- **Monitoring**: Health endpoints and metrics collection

## 🔧 Configuration

### Environment Variables
See `.env.example` for all available configuration options.

Key settings:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection URL
- `RABBITMQ_URL`: RabbitMQ connection URL
- `API_GATEWAY_PORT`: API Gateway port (default: 8000)
- `ENVIRONMENT`: development/production

### Multi-tenant Configuration
- **Schema Isolation**: Each tenant has a separate PostgreSQL schema
- **API Key Authentication**: Tenant-specific API keys with permissions
- **Rate Limiting**: Configurable limits per tenant
- **Resource Quotas**: Configurable resource limits per tenant

## 📊 Monitoring & Observability

### Health Endpoints
```bash
# Service health
GET /health/{service-name}

# Database connectivity
GET /health/database

# Cache status
GET /health/cache

# Queue status
GET /health/queue
```

### Metrics (Future Enhancement)
- Request latency and throughput
- Error rates by service
- Database query performance
- Cache hit/miss ratios
- Queue processing rates

### Logging
- Structured JSON logging
- Configurable log levels
- Centralized log aggregation (future)
- Audit logging for security events

## 🔒 Security

### Authentication & Authorization
- **API Key Authentication**: Secure key-based authentication
- **Tenant Isolation**: Complete data isolation between tenants
- **Permission System**: Granular permissions for API keys
- **Rate Limiting**: Protection against abuse

### Data Protection
- **Encryption**: Data encryption at rest and in transit
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: Parameterized queries
- **CORS Configuration**: Configurable cross-origin policies

### Production Security
- **HTTPS Only**: SSL/TLS encryption required
- **Security Headers**: OWASP recommended headers
- **API Versioning**: Versioned APIs for backward compatibility
- **Audit Logging**: Complete audit trail of operations

## 🧪 Testing

### Automated Testing
```bash
# Run all tests
./test-system.sh

# Run with performance tests
RUN_PERFORMANCE_TESTS=true ./test-system.sh

# Test specific functionality
python -m pytest tests/test_route_search.py -v
```

### Test Coverage
- Unit tests for all services
- Integration tests for service communication
- End-to-end API tests
- Performance and load testing
- Multi-tenant isolation tests

### Test Data
- Sample railway network data
- Test tenants and API keys
- Mock external service responses
- Performance benchmarking data

## 📚 SDKs & Integrations

### Python SDK
```python
from railway_os_sdk import RailwayOSClient

client = RailwayOSClient("api-key", "tenant-id")
routes = client.search_routes("Delhi", "Mumbai", "2024-01-15")
```

Installation:
```bash
pip install -e sdk/python/
```

### JavaScript SDK (Planned)
```javascript
import { RailwayOSClient } from 'railway-os-sdk';

const client = new RailwayOSClient('api-key', 'tenant-id');
const routes = await client.searchRoutes('Delhi', 'Mumbai', '2024-01-15');
```

### REST API Integration
```bash
# Direct API calls
curl -X POST http://localhost:8000/api/v1/routes/search \
  -H "X-API-Key: your-key" \
  -H "X-Tenant-ID: your-tenant" \
  -H "Content-Type: application/json" \
  -d '{"origin": "Delhi", "destination": "Mumbai", "date": "2024-01-15"}'
```

## 🔄 Data Migration

### From Existing Systems
```bash
# Migrate SQLite data to PostgreSQL
python scripts/migrate_data.py --source sqlite.db --target postgres://...

# Validate migration
python scripts/validate_migration.py
```

### Schema Evolution
- **Backward Compatibility**: API versioning for smooth transitions
- **Zero-downtime Migrations**: Database migrations with rollback support
- **Data Validation**: Automated validation of migrated data

## 🚀 Scaling & Performance

### Horizontal Scaling
```bash
# Scale route service
docker-compose up -d --scale route-service=5

# Scale worker service
docker-compose up -d --scale worker-service=10
```

### Performance Optimization
- **Caching Strategy**: Redis caching for frequent queries
- **Database Indexing**: Optimized indexes for route searches
- **Async Processing**: Background processing for heavy operations
- **Connection Pooling**: Efficient database connection management

### Benchmarking
```bash
# Performance testing
ab -n 1000 -c 10 http://localhost:8000/api/v1/routes/search

# Load testing with custom script
python scripts/load_test.py --concurrency 50 --requests 10000
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`./test-system.sh`)
6. Update documentation
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Standards
- **PEP 8**: Python code style guidelines
- **Type Hints**: Full type annotation coverage
- **Documentation**: Comprehensive docstrings
- **Testing**: 80%+ test coverage required

### Commit Guidelines
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Keep commits focused on single changes
- Squash related commits before merging

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker resources
docker system df

# View service logs
docker-compose logs api-gateway

# Check environment variables
cat .env | grep -v PASSWORD
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec postgres psql -U railway_user -d railway_os -c "SELECT 1;"

# Check database logs
docker-compose logs postgres
```

#### Route Search Failures
```bash
# Check route service health
curl http://localhost:8002/health

# Validate input data
curl -X POST http://localhost:8002/api/v1/routes/search \
  -H "Content-Type: application/json" \
  -d '{"origin": "Delhi", "destination": "Mumbai", "date": "2024-01-15"}'
```

### Getting Help
- 📖 **Documentation**: https://docs.railwayos.com
- 🐛 **Bug Reports**: https://github.com/railway-os/platform/issues
- 💬 **Discussions**: https://github.com/railway-os/platform/discussions
- 📧 **Email Support**: support@railwayos.com

## 🗺️ Roadmap

### Phase 1 ✅ (Completed)
- [x] Microservices architecture implementation
- [x] Multi-tenant database schema
- [x] API Gateway with authentication
- [x] Route finding engine
- [x] Async job processing
- [x] Docker containerization
- [x] Python SDK

### Phase 2 🔄 (In Progress)
- [ ] JavaScript/TypeScript SDK
- [ ] Comprehensive monitoring with Prometheus/Grafana
- [ ] Advanced caching strategies
- [ ] Real-time route updates
- [ ] Enhanced security features

### Phase 3 📋 (Planned)
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Integration with railway company systems
- [ ] Machine learning for route optimization
- [ ] Multi-language support
- [ ] Global railway network coverage

## 🙏 Acknowledgments

- Railway companies for domain expertise
- Open source community for amazing tools
- Contributors and early adopters

---

**Railway Operating System** - Transforming railway operations through technology.