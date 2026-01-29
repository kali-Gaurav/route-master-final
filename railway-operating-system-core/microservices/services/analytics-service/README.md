# Analytics Service

Comprehensive data analytics and business intelligence service for the Railway Operating System. Provides advanced analytics, real-time dashboards, reporting, and business intelligence capabilities.

## Features

### 1. **Real-Time Analytics**
- Route popularity analysis
- Transfer pattern analysis
- Peak hours detection
- Station connectivity mapping
- Geographic distribution analysis

### 2. **Performance Monitoring**
- API response time tracking
- Endpoint performance metrics
- Cache hit rate analysis
- Error rate monitoring
- System health dashboards

### 3. **Business Intelligence**
- Revenue analytics
- User engagement metrics
- Geographic analysis
- Trend analysis
- KPI tracking

### 4. **Advanced Reporting**
- Route performance reports
- System health reports
- Business intelligence reports
- User engagement reports
- Custom report generation

### 5. **Dashboards**
- Overview dashboard (key metrics)
- Performance dashboard (system health)
- Route dashboard (route analytics)
- Business dashboard (business metrics)

### 6. **Data Export**
- CSV export
- JSON export
- Excel export (via OpenPyXL)
- PDF reports

### 7. **Alerting System**
- Configurable alerts
- Multiple notification channels (email, Slack, webhooks)
- Alert history tracking
- Cooldown periods to prevent alert spam

## Architecture

### Service Components

```
analytics-service/
├── main.py                 # FastAPI application and endpoints
├── models.py              # SQLAlchemy models for analytics data
├── dashboard.py           # Dashboard configuration and rendering
├── etl_pipeline.py        # Data aggregation and ETL pipeline
├── __init__.py            # Package initialization
└── requirements.txt       # Service dependencies
```

### Database Tables

#### Analytics Data Tables
- `analytics_metrics` - Computed analytics metrics
- `analytics_reports` - Generated reports
- `analytics_dashboards` - Dashboard configurations
- `analytics_queries` - Cached analytics queries

#### Metrics Collection Tables
- `api_metrics` - API performance metrics
- `route_search_metrics` - Route search performance
- `cache_metrics` - Cache performance data
- `user_engagement` - User engagement metrics
- `user_locations` - Geographic location data

#### Business Intelligence Tables
- `business_metrics` - KPI and business metrics
- `alert_configurations` - Alert configurations
- `alert_history` - Alert trigger history

#### Data Export Tables
- `data_exports` - Track export operations

## API Endpoints

### Analytics Endpoints

#### Query Analytics
```
POST /v1/analytics/query
Request:
{
  "tenant_id": "uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": ["route_popularity"],
  "group_by": ["origin_station"],
  "limit": 100
}

Response:
{
  "data": [...],
  "total_count": 50,
  "summary": {...},
  "metadata": {...}
}
```

#### Get Dashboard Data
```
GET /v1/dashboard/{dashboard_type}?tenant_id={id}&date_range=30d

Supported dashboard_types:
- overview
- performance
- routes
- business
```

#### Generate Reports
```
POST /v1/reports/generate
Request:
{
  "tenant_id": "uuid",
  "report_type": "route_performance|system_performance|business_intelligence",
  "format": "json|csv|excel|pdf",
  "parameters": {},
  "email_recipients": ["email@example.com"]
}

Response:
{
  "report_id": "...",
  "report_type": "...",
  "generated_at": "2024-01-31T10:00:00Z",
  "data": {...},
  "email_sent": true
}
```

#### Get Metrics
```
GET /v1/analytics/metrics?tenant_id={id}&metric_names=total_searches&metric_names=avg_response_time

Response:
[
  {
    "metric_name": "total_searches",
    "value": 1250,
    "change_percentage": 5.2,
    "trend": "up",
    "period": "2024-01-01 to 2024-01-31"
  }
]
```

#### Export Data
```
GET /v1/analytics/export/{export_type}?tenant_id={id}&start_date=2024-01-01&end_date=2024-01-31

Supported export_types:
- route_analytics
- performance_metrics

Returns: CSV or JSON file download
```

#### Health Check
```
GET /health

Response:
{
  "status": "healthy",
  "service": "analytics-service",
  "timestamp": "2024-01-31T10:00:00Z"
}
```

## Analytics Engine

### AnalyticsEngine Class

The main analytics engine provides methods for:

#### `get_route_analytics(tenant_id, start_date, end_date)`
Retrieves comprehensive route analytics including:
- Route popularity rankings
- Transfer pattern analysis
- Peak hours distribution
- Station connectivity metrics

#### `get_performance_metrics(tenant_id, start_date, end_date)`
Gets system performance metrics:
- API response times
- Error rates
- Cache performance
- Percentile latencies (p95, p99)

#### `get_business_analytics(tenant_id, start_date, end_date)`
Provides business intelligence:
- Revenue analytics
- User engagement metrics
- Geographic analysis

#### `generate_report(tenant_id, report_type, parameters)`
Generates comprehensive reports for:
- Route performance
- System performance
- Business intelligence

#### `get_dashboard_data(tenant_id, dashboard_type, date_range)`
Returns formatted data for dashboard visualizations

## ETL Pipeline

### AnalyticsETLPipeline Class

Handles data aggregation and processing:

#### `aggregate_daily_metrics(tenant_id, date)`
Aggregates metrics for a specific day:
- Route search aggregations
- API metrics aggregations
- Cache performance aggregations

#### `backfill_analytics(tenant_id, start_date, end_date)`
Backfills analytics data for a date range

### DataQualityChecker Class

Validates data quality:

#### `validate_metrics(tenant_id)`
Performs comprehensive validation:
- Null value checks
- Data consistency validation
- Outlier detection
- Statistical analysis

## Dashboard Templates

### Overview Dashboard
- Total searches metric
- Average route score
- Cache hit rate
- Route popularity chart
- Peak hours line chart
- Transfer distribution pie chart

### Performance Dashboard
- Average response time
- Error rate
- API endpoint performance
- Cache hit rates over time

### Routes Dashboard
- Top 20 routes table
- Station connectivity network visualization

### Business Dashboard
- Monthly search volume
- User engagement by type
- Geographic distribution map

## Configuration

The service uses the shared configuration system:

```python
from shared.config import DATABASE_CONFIG, API_CONFIG

# Database configuration (multi-tenant schema-per-tenant)
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'password',
    'database': 'railway_os'
}

# API configuration
API_CONFIG = {
    'port': 8084,
    'host': '0.0.0.0',
    'debug_mode': False,
    'log_level': 'INFO'
}
```

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/railway_os"
export REDIS_URL="redis://localhost:6379/0"
export API_PORT=8084
export DEBUG_MODE=false
```

### 3. Initialize Database
```python
from services.analytics_service.models import create_analytics_tables
from shared.models import DatabaseManager

db_manager = DatabaseManager()
create_analytics_tables(db_manager.engine)
```

### 4. Run Service
```bash
# Development
python services/analytics-service/main.py

# Production
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8084 services.analytics_service.main:app
```

## Docker Deployment

### Build Image
```bash
docker build -f Dockerfile.analytics -t railway-os-analytics:latest .
```

### Run Container
```bash
docker run -d \
  --name analytics-service \
  -p 8084:8084 \
  -e DATABASE_URL="postgresql://user:password@postgres:5432/railway_os" \
  -e REDIS_URL="redis://redis:6379/0" \
  railway-os-analytics:latest
```

### Docker Compose
```yaml
analytics-service:
  build:
    context: .
    dockerfile: Dockerfile.analytics
  container_name: analytics-service
  ports:
    - "8084:8084"
  environment:
    DATABASE_URL: postgresql://user:password@postgres:5432/railway_os
    REDIS_URL: redis://redis:6379/0
    DEBUG_MODE: "false"
  depends_on:
    - postgres
    - redis
  networks:
    - railway_network
```

## Performance Optimization

### 1. Query Optimization
- Indexed tables on frequent query columns
- Aggregated metrics pre-computed daily
- Query result caching with Redis

### 2. Data Aggregation
- Automatic daily metric aggregation
- Hourly summaries for frequently accessed data
- Data retention policies to manage table sizes

### 3. Caching Strategy
- Redis caching for frequently accessed analytics
- Cache invalidation on data updates
- TTL-based cache expiration

### 4. Background Tasks
- Asynchronous report generation
- Scheduled daily aggregations
- Email delivery via background tasks

## Monitoring & Debugging

### Service Health
```
GET /health
```

### Logs
```bash
# View logs
docker logs analytics-service

# Stream logs
docker logs -f analytics-service
```

### Metrics Validation
```python
from services.analytics_service.etl_pipeline import DataQualityChecker

checker = DataQualityChecker(db_manager)
validation = await checker.validate_metrics(tenant_id)
print(validation)
```

## Usage Examples

### Get Route Analytics
```python
import httpx
from uuid import UUID

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8084/v1/analytics/query",
        json={
            "tenant_id": str(tenant_id),
            "metrics": ["route_popularity"],
            "limit": 20
        }
    )
    data = response.json()
```

### Generate Report
```python
response = await client.post(
    "http://localhost:8084/v1/reports/generate",
    json={
        "tenant_id": str(tenant_id),
        "report_type": "route_performance",
        "format": "json",
        "email_recipients": ["admin@example.com"]
    }
)
```

### Get Dashboard Data
```python
response = await client.get(
    "http://localhost:8084/v1/dashboard/overview",
    params={
        "tenant_id": str(tenant_id),
        "date_range": "30d"
    }
)
```

## Integration with Other Services

The Analytics Service integrates with:

1. **API Gateway** - Collects API metrics
2. **Route Service** - Gets route search analytics
3. **Data Service** - Stores analyzed data
4. **Auth Service** - Validates tenant access
5. **Monitoring Service** - Reports health metrics

## Best Practices

1. **Multi-Tenancy**: Always provide `tenant_id` for all queries
2. **Date Ranges**: Specify reasonable date ranges to avoid excessive computation
3. **Caching**: Leverage cached results for frequently accessed metrics
4. **Background Processing**: Use background tasks for report generation
5. **Alert Configuration**: Set appropriate thresholds and cooldown periods
6. **Data Retention**: Implement data retention policies for old metrics

## Future Enhancements

- [ ] Predictive analytics with ML models
- [ ] Real-time streaming analytics (Kafka integration)
- [ ] Advanced time-series forecasting
- [ ] Custom metric builder UI
- [ ] Anomaly detection algorithms
- [ ] Integration with BI tools (Tableau, Power BI)
- [ ] GraphQL API for analytics queries
- [ ] Mobile dashboard application
- [ ] Automated report scheduling
- [ ] A/B testing analytics

## Contributing

Contributions are welcome! Please follow the existing code style and include tests for new features.

## License

This project is part of the Railway Operating System and follows the main project's license.