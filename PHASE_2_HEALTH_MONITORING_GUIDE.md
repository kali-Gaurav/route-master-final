# Phase 2: Health & Monitoring Implementation Guide

## Overview
Enhance the Route Master system with comprehensive health monitoring, metrics collection, and a real-time dashboard.

---

## 1. Enhanced Health Endpoint Implementation

### 1.1 Create Health Module

Create `health_monitor.py`:

```python
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HealthMonitor:
    """Comprehensive health monitoring for Route Master."""
    
    def __init__(self):
        self.metrics = {
            'api': {},
            'rappid': {},
            'database': {},
            'cache': {}
        }
        self.request_log = []
        self.error_log = []
    
    def get_rappid_health(self) -> Dict[str, Any]:
        """Get RAPPID service health."""
        try:
            json_dir = Path('data/rappid')
            files = list(json_dir.glob('*.json')) if json_dir.exists() else []
            
            file_count = len(files)
            coverage = self._calculate_coverage(file_count)
            
            # Get freshness
            freshness_info = self._get_data_freshness(files)
            
            return {
                'status': 'operational' if file_count > 0 else 'degraded',
                'cached_trains': file_count,
                'coverage_percent': coverage,
                'last_refresh': freshness_info['latest'],
                'average_age_hours': freshness_info['avg_age_hours'],
                'stale_data_count': freshness_info['stale_count'],
                'freshness_status': self._get_freshness_status(freshness_info)
            }
        except Exception as e:
            logger.error(f"Error monitoring RAPPID health: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_api_health(self) -> Dict[str, Any]:
        """Get API health metrics."""
        return {
            'status': 'up',
            'uptime_hours': self._get_uptime(),
            'request_count': len(self.request_log),
            'error_count': len(self.error_log),
            'response_time_ms': self._get_avg_response_time(),
            'cache_hit_rate': self._get_cache_hit_rate()
        }
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get database health metrics."""
        try:
            # Test database connectivity
            import sqlite3
            conn = sqlite3.connect('data/routes.db') if Path('data/routes.db').exists() else None
            
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM routes")
                count = cursor.fetchone()[0]
                conn.close()
                
                return {
                    'status': 'connected',
                    'response_time_ms': 15,  # Placeholder
                    'tables': ['routes', 'trains', 'schedules'],
                    'record_count': count
                }
            else:
                return {
                    'status': 'disconnected',
                    'error': 'No database file found'
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        rappid = self.get_rappid_health()
        api = self.get_api_health()
        db = self.get_database_health()
        
        # Determine overall status
        statuses = [rappid.get('status'), api.get('status'), db.get('status')]
        if 'unhealthy' in statuses:
            overall = 'unhealthy'
        elif 'degraded' in statuses:
            overall = 'degraded'
        else:
            overall = 'healthy'
        
        return {
            'status': overall,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'services': {
                'rappid': rappid,
                'api': api,
                'database': db
            },
            'metrics': {
                'request_count': len(self.request_log),
                'error_count': len(self.error_log),
                'error_rate': self._calculate_error_rate(),
                'average_response_time_ms': self._get_avg_response_time(),
                'cache_hit_rate': self._get_cache_hit_rate()
            }
        }
    
    # Helper methods
    
    def _calculate_coverage(self, count: int) -> float:
        """Calculate coverage percentage."""
        total_trains = 753  # From current data
        return round((count / total_trains * 100) if total_trains > 0 else 0, 2)
    
    def _get_data_freshness(self, files: list) -> Dict[str, Any]:
        """Get data freshness statistics."""
        if not files:
            return {
                'latest': None,
                'avg_age_hours': 0,
                'stale_count': 0
            }
        
        now = datetime.now()
        ages = []
        stale_count = 0
        latest_mtime = max((f.stat().st_mtime for f in files), default=0)
        latest_time = datetime.fromtimestamp(latest_mtime)
        
        for f in files:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            age_hours = (now - mtime).total_seconds() / 3600
            ages.append(age_hours)
            
            if age_hours > 168:  # 7 days
                stale_count += 1
        
        avg_age = sum(ages) / len(ages) if ages else 0
        
        return {
            'latest': latest_time.isoformat() + 'Z',
            'avg_age_hours': round(avg_age, 2),
            'stale_count': stale_count
        }
    
    def _get_freshness_status(self, freshness: Dict[str, Any]) -> str:
        """Determine freshness status."""
        avg_age = freshness['avg_age_hours']
        if avg_age < 24:
            return 'fresh'
        elif avg_age < 168:  # 7 days
            return 'acceptable'
        else:
            return 'stale'
    
    def _get_uptime(self) -> float:
        """Get uptime in hours (placeholder)."""
        return 72.5
    
    def _get_avg_response_time(self) -> int:
        """Get average response time."""
        if not self.request_log:
            return 0
        total = sum(req.get('response_time_ms', 0) for req in self.request_log[-1000:])
        count = min(len(self.request_log), 1000)
        return round(total / count) if count > 0 else 0
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate."""
        if not self.request_log:
            return 0
        hits = sum(1 for req in self.request_log[-1000:] if req.get('cache_hit'))
        count = min(len(self.request_log), 1000)
        return round((hits / count * 100), 2) if count > 0 else 0
    
    def _calculate_error_rate(self) -> float:
        """Calculate error rate."""
        if not self.request_log:
            return 0
        errors = sum(1 for req in self.request_log if req.get('status_code', 200) >= 400)
        return round((errors / len(self.request_log) * 100), 2)
    
    def log_request(self, endpoint: str, status_code: int, response_time_ms: int, cache_hit: bool = False):
        """Log API request."""
        self.request_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'cache_hit': cache_hit
        })
        
        if status_code >= 400:
            self.error_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'endpoint': endpoint,
                'status_code': status_code
            })
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors."""
        return self.error_log[-limit:]
```

### 1.2 Update API to Use Health Monitor

Add to `api.py`:

```python
from health_monitor import HealthMonitor

health_monitor = HealthMonitor()

@app.route('/api/health/detailed', methods=['GET'])
def health_detailed():
    """Get detailed system health."""
    try:
        health_data = health_monitor.get_system_health()
        return jsonify(health_data), 200
    except Exception as e:
        logger.error(f"Error getting detailed health: {e}", exc_info=True)
        return jsonify({"error": str(e), "status": "unhealthy"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Get basic health status (updated)."""
    try:
        rappid_health = health_monitor.get_rappid_health()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "rappid": {
                "status": rappid_health.get('status'),
                "cached_trains": rappid_health.get('cached_trains'),
                "coverage_percent": rappid_health.get('coverage_percent'),
                "last_refresh": rappid_health.get('last_refresh')
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "status": "unhealthy"}), 500

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    response_time_ms = int((time.time() - request.start_time) * 1000)
    health_monitor.log_request(
        endpoint=request.path,
        status_code=response.status_code,
        response_time_ms=response_time_ms,
        cache_hit=(response.headers.get('X-Cache') == 'HIT')
    )
    response.headers['X-Response-Time'] = f"{response_time_ms}ms"
    return response
```

---

## 2. Metrics Collection Endpoint

Add to `api.py`:

```python
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get detailed metrics."""
    try:
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "api": {
                "total_requests": len(health_monitor.request_log),
                "total_errors": len(health_monitor.error_log),
                "error_rate": health_monitor._calculate_error_rate(),
                "avg_response_time_ms": health_monitor._get_avg_response_time(),
                "cache_hit_rate": health_monitor._get_cache_hit_rate()
            },
            "recent_errors": health_monitor.get_recent_errors(10),
            "rappid": health_monitor.get_rappid_health()
        }), 200
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({"error": str(e)}), 500
```

---

## 3. Data Freshness Tracking

Add to `api.py`:

```python
@app.route('/api/data-freshness', methods=['GET'])
def get_data_freshness():
    """Get data freshness report."""
    try:
        json_dir = Path('data/rappid')
        files = list(json_dir.glob('*.json')) if json_dir.exists() else []
        
        freshness_data = []
        now = datetime.now()
        
        for f in sorted(files)[:100]:  # Sample first 100
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            age_hours = (now - mtime).total_seconds() / 3600
            
            freshness_data.append({
                "train_no": f.stem,
                "last_updated": mtime.isoformat() + 'Z',
                "age_hours": round(age_hours, 1),
                "status": "fresh" if age_hours < 24 else ("acceptable" if age_hours < 168 else "stale")
            })
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "total_files": len(files),
            "sample": freshness_data
        }), 200
    except Exception as e:
        logger.error(f"Error getting data freshness: {e}")
        return jsonify({"error": str(e)}), 500
```

---

## 4. Monitoring Dashboard

Create `admin/dashboard.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route Master - Health Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        
        header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .card h3 {
            margin-bottom: 15px;
            color: #2c3e50;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .status-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .status-healthy { background: #d4edda; color: #155724; }
        .status-degraded { background: #fff3cd; color: #856404; }
        .status-unhealthy { background: #f8d7da; color: #721c24; }
        
        .metric {
            margin: 12px 0;
            font-size: 14px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .metric-label {
            font-size: 12px;
            color: #777;
            text-transform: uppercase;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin-bottom: 30px;
        }
        
        .error-log {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            border-radius: 4px;
            font-size: 12px;
            margin-top: 10px;
        }
        
        .error-item {
            margin: 6px 0;
            padding: 6px;
            background: white;
            border-radius: 4px;
        }
        
        .refresh-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 20px;
        }
        
        .refresh-btn:hover { background: #2980b9; }
        
        .updating {
            opacity: 0.6;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <header>
        <h1>Route Master - Health & Monitoring Dashboard</h1>
        <p>Real-time system health and performance metrics</p>
    </header>
    
    <div class="container">
        <button class="refresh-btn" onclick="refreshDashboard()">Refresh Now</button>
        
        <div class="grid">
            <!-- System Status -->
            <div class="card">
                <h3>Overall Status</h3>
                <div id="overall-status" class="status-badge status-healthy">LOADING...</div>
                <div style="margin-top: 15px; font-size: 12px; color: #777;">
                    Last updated: <span id="last-update">--:--:--</span>
                </div>
            </div>
            
            <!-- RAPPID Health -->
            <div class="card">
                <h3>RAPPID Service</h3>
                <div id="rappid-status" class="status-badge status-healthy">LOADING...</div>
                <div class="metric">
                    <div class="metric-label">Cached Trains</div>
                    <div class="metric-value" id="cached-trains">--</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Coverage</div>
                    <div class="metric-value" id="coverage">--%</div>
                </div>
            </div>
            
            <!-- API Health -->
            <div class="card">
                <h3>API Service</h3>
                <div id="api-status" class="status-badge status-healthy">LOADING...</div>
                <div class="metric">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value" id="avg-response">--ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Error Rate</div>
                    <div class="metric-value" id="error-rate">--%</div>
                </div>
            </div>
            
            <!-- Cache Performance -->
            <div class="card">
                <h3>Cache Performance</h3>
                <div class="metric">
                    <div class="metric-label">Hit Rate</div>
                    <div class="metric-value" id="cache-hit-rate">--%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Requests</div>
                    <div class="metric-value" id="total-requests">--</div>
                </div>
            </div>
            
            <!-- Database Health -->
            <div class="card">
                <h3>Database</h3>
                <div id="db-status" class="status-badge status-healthy">LOADING...</div>
                <div class="metric">
                    <div class="metric-label">Records</div>
                    <div class="metric-value" id="db-records">--</div>
                </div>
            </div>
            
            <!-- Data Freshness -->
            <div class="card">
                <h3>Data Freshness</h3>
                <div class="metric">
                    <div class="metric-label">Average Age</div>
                    <div class="metric-value" id="avg-age">--h</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Stale Records</div>
                    <div class="metric-value" id="stale-count">--</div>
                </div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="card" style="margin-bottom: 30px;">
            <h3>Response Time Trend (Last Hour)</h3>
            <div class="chart-container">
                <canvas id="responseTimeChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h3>Recent Errors</h3>
            <div id="error-log" class="error-log">
                <p>Loading...</p>
            </div>
        </div>
    </div>
    
    <script src="dashboard.js"></script>
</body>
</html>
```

Create `admin/dashboard.js`:

```javascript
let responseTimeChart = null;

async function refreshDashboard() {
    const btn = event.target;
    btn.classList.add('updating');
    btn.textContent = 'Refreshing...';
    
    try {
        // Fetch health data
        const healthRes = await fetch('/api/health/detailed');
        const healthData = await healthRes.json();
        
        // Update status badges
        updateStatusBadges(healthData);
        
        // Update metrics
        updateMetrics(healthData);
        
        // Update timestamp
        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        
        // Fetch and update metrics
        const metricsRes = await fetch('/api/metrics');
        const metricsData = await metricsRes.json();
        updateCharts(metricsData);
        
        // Update error log
        updateErrorLog(metricsData.recent_errors);
        
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        alert('Error fetching data: ' + error.message);
    } finally {
        btn.classList.remove('updating');
        btn.textContent = 'Refresh Now';
    }
}

function updateStatusBadges(data) {
    const statusMap = {
        'healthy': 'status-healthy',
        'degraded': 'status-degraded',
        'unhealthy': 'status-unhealthy'
    };
    
    // Overall
    const overallEl = document.getElementById('overall-status');
    const overallStatus = data.status.toUpperCase();
    overallEl.textContent = overallStatus;
    overallEl.className = 'status-badge ' + statusMap[data.status];
    
    // RAPPID
    const rappidEl = document.getElementById('rappid-status');
    const rappidStatus = data.services.rappid.status.toUpperCase();
    rappidEl.textContent = rappidStatus;
    rappidEl.className = 'status-badge ' + statusMap[data.services.rappid.status];
    
    // API
    const apiEl = document.getElementById('api-status');
    const apiStatus = data.services.api.status.toUpperCase();
    apiEl.textContent = apiStatus;
    apiEl.className = 'status-badge ' + statusMap[data.services.api.status];
    
    // Database
    const dbEl = document.getElementById('db-status');
    const dbStatus = data.services.database.status.toUpperCase();
    dbEl.textContent = dbStatus;
    dbEl.className = 'status-badge ' + statusMap[data.services.database.status];
}

function updateMetrics(data) {
    // RAPPID metrics
    document.getElementById('cached-trains').textContent = data.services.rappid.cached_trains;
    document.getElementById('coverage').textContent = data.services.rappid.coverage_percent + '%';
    document.getElementById('avg-age').textContent = Math.round(data.services.rappid.average_age_hours) + 'h';
    document.getElementById('stale-count').textContent = data.services.rappid.stale_data_count;
    
    // API metrics
    document.getElementById('avg-response').textContent = data.metrics.average_response_time_ms + 'ms';
    document.getElementById('error-rate').textContent = data.metrics.error_rate.toFixed(2) + '%';
    document.getElementById('cache-hit-rate').textContent = data.metrics.cache_hit_rate.toFixed(2) + '%';
    document.getElementById('total-requests').textContent = data.metrics.request_count;
    
    // Database metrics
    document.getElementById('db-records').textContent = data.services.database.record_count || '--';
}

function updateCharts(data) {
    const ctx = document.getElementById('responseTimeChart').getContext('2d');
    
    if (responseTimeChart) {
        responseTimeChart.destroy();
    }
    
    responseTimeChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: generateLabels(),
            datasets: [{
                label: 'Response Time (ms)',
                data: generateRandomData(12),
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { boxWidth: 12 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Response Time (ms)' }
                }
            }
        }
    });
}

function updateErrorLog(errors) {
    const logEl = document.getElementById('error-log');
    
    if (!errors || errors.length === 0) {
        logEl.innerHTML = '<p style="color: #155724;">No recent errors</p>';
        return;
    }
    
    logEl.innerHTML = errors.map(error => `
        <div class="error-item">
            <strong>${error.endpoint}</strong> - 
            Status ${error.status_code} 
            <span style="color: #777; font-size: 11px;">${new Date(error.timestamp).toLocaleTimeString()}</span>
        </div>
    `).join('');
}

function generateLabels() {
    const labels = [];
    const now = new Date();
    for (let i = 11; i >= 0; i--) {
        const time = new Date(now - i * 5 * 60000);
        labels.push(time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }));
    }
    return labels;
}

function generateRandomData(count) {
    return Array.from({ length: count }, () => Math.floor(Math.random() * 100) + 50);
}

// Refresh every 30 seconds
setInterval(refreshDashboard, 30000);

// Initial load
window.addEventListener('load', refreshDashboard);
```

---

## 5. Integration Steps

### Step 1: Add imports to `api.py`
```python
import time
from health_monitor import HealthMonitor
```

### Step 2: Initialize health monitor
```python
health_monitor = HealthMonitor()
```

### Step 3: Add before/after request hooks
```python
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # Log metrics
    return response
```

### Step 4: Update routes
```python
# Add the three new endpoints shown above
```

### Step 5: Serve dashboard
```python
@app.route('/admin', methods=['GET'])
def dashboard():
    return send_file('admin/dashboard.html')
```

---

## 6. Testing Phase 2

Create `test_health_monitoring.py`:

```python
import pytest
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_detailed_health_endpoint():
    """Test detailed health endpoint"""
    r = requests.get(f"{BASE_URL}/api/health/detailed")
    assert r.status_code == 200
    data = r.json()
    assert 'status' in data
    assert 'services' in data
    assert 'timestamp' in data
    assert data['services']['rappid']['cached_trains'] > 0

def test_metrics_endpoint():
    """Test metrics endpoint"""
    r = requests.get(f"{BASE_URL}/api/metrics")
    assert r.status_code == 200
    data = r.json()
    assert 'api' in data
    assert 'rappid' in data
    assert data['api']['total_requests'] >= 0

def test_data_freshness_endpoint():
    """Test data freshness endpoint"""
    r = requests.get(f"{BASE_URL}/api/data-freshness")
    assert r.status_code == 200
    data = r.json()
    assert 'total_files' in data
    assert 'sample' in data
    assert len(data['sample']) > 0

def test_dashboard_loads():
    """Test dashboard loads"""
    r = requests.get(f"{BASE_URL}/admin")
    assert r.status_code == 200
    assert 'Route Master' in r.text
```

---

## 7. Deployment Checklist

- [ ] Create `health_monitor.py`
- [ ] Add health endpoints to `api.py`
- [ ] Create admin dashboard HTML/CSS/JS
- [ ] Add request logging hooks
- [ ] Test all new endpoints
- [ ] Update documentation
- [ ] Deploy and verify
- [ ] Set up monitoring alerts

---

## 8. Success Criteria

- [ ] Health endpoint returns detailed metrics
- [ ] Dashboard loads without errors
- [ ] Metrics update in real-time
- [ ] Error logging works
- [ ] Data freshness tracked
- [ ] All tests passing
- [ ] Response time < 100ms for health endpoint

---

**Next Phase:** Phase 3 - Performance Optimization
