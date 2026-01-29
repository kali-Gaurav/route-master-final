# Analytics Service API Documentation

## Overview

The Analytics Service provides RESTful APIs for accessing real-time analytics, dashboards, reports, and business intelligence metrics for the Railway Operating System.

**Base URL**: `http://analytics-service:8084/v1`

**Authentication**: Bearer token via API Key (through API Gateway)

## API Reference

### 1. Analytics Query Endpoint

Execute custom analytics queries with flexible filtering and aggregation.

#### Request

```http
POST /v1/analytics/query
Content-Type: application/json

{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "metrics": ["route_popularity"],
  "dimensions": ["origin_station"],
  "filters": {
    "transfer_count": {"$lte": 2}
  },
  "group_by": ["origin_station", "destination_station"],
  "limit": 50,
  "offset": 0
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tenant_id | UUID | Yes | Tenant identifier |
| start_date | date | No | Start date (YYYY-MM-DD) |
| end_date | date | No | End date (YYYY-MM-DD) |
| metrics | string[] | Yes | Metrics to retrieve |
| dimensions | string[] | No | Grouping dimensions |
| filters | object | No | Query filters |
| group_by | string[] | No | Group by columns |
| limit | integer | No | Max results (default: 100) |
| offset | integer | No | Pagination offset (default: 0) |

#### Response

```json
{
  "data": [
    {
      "origin_station": "A",
      "destination_station": "B",
      "search_count": 1250,
      "avg_score": 4.5,
      "min_score": 3.2,
      "max_score": 5.0
    }
  ],
  "total_count": 1,
  "summary": {
    "total_searches": 1250,
    "average_score": 4.5
  },
  "metadata": {
    "query_type": "route_popularity",
    "execution_time_ms": 125
  }
}
```

#### Error Response

```json
{
  "error": {
    "code": "INVALID_METRIC",
    "message": "Metric 'unknown_metric' not supported",
    "status": 400
  }
}
```

---

### 2. Dashboard Endpoint

Get pre-formatted dashboard data for visualizations.

#### Request

```http
GET /v1/dashboard/{dashboard_type}?tenant_id={tenant_id}&date_range={range}
```

#### Path Parameters

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| dashboard_type | string | Yes | `overview`, `performance`, `routes`, `business` |

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| tenant_id | UUID | - | Tenant identifier |
| date_range | string | 30d | `7d`, `30d`, `90d`, `1y` |
| include_trends | boolean | true | Include trend analysis |

#### Response - Overview Dashboard

```json
{
  "total_searches": 12500,
  "avg_route_score": 4.35,
  "total_stations": 250,
  "avg_response_time": 145.2,
  "cache_hit_rate": 82.5,
  "charts": {
    "route_popularity": [
      {
        "origin_station": "Delhi",
        "destination_station": "Mumbai",
        "search_count": 1250,
        "avg_score": 4.6
      }
    ],
    "peak_hours": [
      {
        "hour": 9,
        "searches": 450,
        "avg_score": 4.4
      }
    ],
    "transfer_distribution": [
      {
        "transfers": 0,
        "route_count": 500,
        "avg_duration_minutes": 120
      }
    ]
  }
}
```

#### Response - Performance Dashboard

```json
{
  "api_performance": [
    {
      "endpoint": "/v1/routes/search",
      "total_requests": 5000,
      "avg_response_time": 145.2,
      "p95_response_time": 285.3,
      "p99_response_time": 425.1,
      "error_count": 12,
      "error_rate": 0.24
    }
  ],
  "route_performance": {
    "total_searches": 5000,
    "avg_search_time": 125.5,
    "successful_searches": 4988,
    "avg_results_per_search": 3.2
  },
  "cache_performance": [
    {
      "cache_type": "redis",
      "total_requests": 8000,
      "cache_hits": 6560,
      "hit_rate_percentage": 82.0
    }
  ]
}
```

---

### 3. Report Generation Endpoint

Generate comprehensive reports in various formats.

#### Request

```http
POST /v1/reports/generate
Content-Type: application/json

{
  "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
  "report_type": "route_performance",
  "format": "json",
  "parameters": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "email_recipients": ["admin@example.com"]
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tenant_id | UUID | Yes | Tenant identifier |
| report_type | string | Yes | Report type (see below) |
| format | string | No | Output format (default: json) |
| parameters | object | No | Report-specific parameters |
| email_recipients | string[] | No | Email addresses for delivery |

#### Supported Report Types

| Type | Description |
|------|-------------|
| `route_performance` | Route analytics and performance metrics |
| `system_performance` | API and system health metrics |
| `business_intelligence` | Revenue and engagement metrics |

#### Supported Formats

| Format | Description |
|--------|-------------|
| `json` | JSON format |
| `csv` | CSV format |
| `excel` | Excel workbook |
| `pdf` | PDF document |

#### Response

```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000_route_performance_2024-01-31T10:00:00Z",
  "report_type": "route_performance",
  "generated_at": "2024-01-31T10:00:00Z",
  "data": {
    "route_popularity": [...],
    "transfer_analysis": [...],
    "peak_hours": [...],
    "station_connectivity": [...]
  },
  "email_sent": true,
  "metadata": {
    "record_count": 250,
    "processing_time_ms": 1250
  }
}
```

---

### 4. Metrics Endpoint

Get specific metrics with trend analysis.

#### Request

```http
GET /v1/analytics/metrics?tenant_id={tenant_id}&metric_names={metric}&metric_names={metric}&start_date={date}&end_date={date}
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tenant_id | UUID | Yes | Tenant identifier |
| metric_names | string[] | Yes | Metric names to retrieve |
| start_date | date | No | Start date (YYYY-MM-DD) |
| end_date | date | No | End date (YYYY-MM-DD) |

#### Supported Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `total_searches` | count | Total route searches |
| `avg_response_time` | duration | Average API response time |
| `cache_hit_rate` | percentage | Cache effectiveness |
| `error_rate` | percentage | System error rate |
| `avg_route_score` | score | Average route quality score |
| `unique_users` | count | Unique user count |
| `station_coverage` | count | Number of stations served |

#### Response

```json
[
  {
    "metric_name": "total_searches",
    "value": 12500,
    "change_percentage": 5.2,
    "trend": "up",
    "period": "2024-01-01 to 2024-01-31"
  },
  {
    "metric_name": "avg_response_time",
    "value": 145.2,
    "change_percentage": -3.1,
    "trend": "down",
    "period": "2024-01-01 to 2024-01-31"
  }
]
```

---

### 5. Data Export Endpoint

Export analytics data in various formats.

#### Request

```http
GET /v1/analytics/export/{export_type}?tenant_id={tenant_id}&start_date={date}&end_date={date}
```

#### Path Parameters

| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| export_type | string | Yes | `route_analytics`, `performance_metrics`, `business_metrics` |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tenant_id | UUID | Yes | Tenant identifier |
| start_date | date | No | Start date (YYYY-MM-DD) |
| end_date | date | No | End date (YYYY-MM-DD) |

#### Response

Returns file download with appropriate Content-Type:
- `route_analytics` → CSV file
- `performance_metrics` → JSON file
- `business_metrics` → Excel file

Example headers:
```http
Content-Type: text/csv
Content-Disposition: attachment; filename=route_analytics.csv
```

---

### 6. Health Check Endpoint

Check service health and status.

#### Request

```http
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "service": "analytics-service",
  "timestamp": "2024-01-31T10:00:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "database_connection": "connected",
  "cache_connection": "connected"
}
```

---

## Request/Response Examples

### Example 1: Get Top Routes

```bash
curl -X POST http://localhost:8084/v1/analytics/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "metrics": ["route_popularity"],
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "limit": 20
  }'
```

### Example 2: Get Performance Dashboard

```bash
curl -X GET "http://localhost:8084/v1/dashboard/performance?tenant_id=550e8400-e29b-41d4-a716-446655440000&date_range=7d" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

### Example 3: Generate Report with Email

```bash
curl -X POST http://localhost:8084/v1/reports/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_type": "route_performance",
    "format": "pdf",
    "parameters": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "email_recipients": ["admin@example.com", "manager@example.com"]
  }'
```

### Example 4: Get Metrics with Trends

```bash
curl -X GET "http://localhost:8084/v1/analytics/metrics?tenant_id=550e8400-e29b-41d4-a716-446655440000&metric_names=total_searches&metric_names=avg_response_time&start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

---

## Error Handling

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400,
    "timestamp": "2024-01-31T10:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "details": {
      "field": "Additional error details"
    }
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_TENANT_ID` | 400 | Invalid or missing tenant ID |
| `INVALID_DATE_RANGE` | 400 | Invalid date range |
| `UNSUPPORTED_METRIC` | 400 | Unsupported metric name |
| `INVALID_REPORT_TYPE` | 400 | Invalid report type |
| `DATABASE_ERROR` | 500 | Database connection error |
| `QUERY_TIMEOUT` | 504 | Query execution timeout |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

The Analytics Service implements rate limiting to prevent abuse:

| Tier | Requests/Minute | Concurrent Queries |
|------|-----------------|-------------------|
| Standard | 100 | 10 |
| Premium | 500 | 50 |
| Enterprise | 2000 | 200 |

Rate limit headers in response:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067260
```

---

## Pagination

For endpoints that return multiple results, use pagination:

```http
GET /v1/analytics/query?limit=50&offset=0
GET /v1/analytics/query?limit=50&offset=50
```

Response includes pagination info:
```json
{
  "data": [...],
  "pagination": {
    "total_count": 1000,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Caching

Some endpoints support caching via HTTP headers:

```http
Cache-Control: max-age=300
ETag: "33a64df5425670"
Last-Modified: "Wed, 31 Jan 2024 10:00:00 GMT"
```

---

## Authentication

All API requests require authentication via API Key:

```http
Authorization: Bearer YOUR_API_TOKEN
```

Obtain API token from the Auth Service and pass it with all requests.

---

## Versioning

The API uses URL versioning:
- Current version: `/v1`
- All endpoints are under `/v1` prefix
- Version will be incremented for breaking changes

---

## CORS Support

The service supports CORS requests from configured origins:

```http
Access-Control-Allow-Origin: https://app.railwayos.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## Webhooks

The Analytics Service can send real-time notifications via webhooks:

```json
POST /webhooks/analytics-event
{
  "event_type": "metric_threshold_exceeded",
  "tenant_id": "uuid",
  "metric": "error_rate",
  "value": 5.2,
  "threshold": 5.0,
  "timestamp": "2024-01-31T10:00:00Z"
}
```

---

## Best Practices

1. **Always include tenant_id** in requests
2. **Use appropriate date ranges** to avoid excessive computation
3. **Implement result caching** on client side
4. **Use pagination** for large result sets
5. **Monitor rate limits** and implement backoff
6. **Handle timeouts** gracefully
7. **Validate input** before sending requests
8. **Use batch operations** when possible
9. **Cache stable metrics** for performance
10. **Monitor API latency** for optimization

---

## Support

For API support and issues:
- Email: support@railwayos.com
- Documentation: [README.md](./README.md)
- Integration Guide: [INTEGRATION.md](./INTEGRATION.md)

---

**Last Updated**: 2024-01-31
**API Version**: 1.0.0
**Service Version**: 1.0.0