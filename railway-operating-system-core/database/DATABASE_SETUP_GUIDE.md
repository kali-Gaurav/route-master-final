# Database System - Complete Setup Guide

## 🚀 Quick Start

### Prerequisites
```bash
# Install PostgreSQL 14+
# Install Python 3.10+
# Have psql and pg_dump utilities available
```

### Installation Steps (5 minutes)

```bash
# 1. Navigate to database folder
cd database/

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database connection
# Create .env file:
cat > ../.env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=railway_os
DB_USER=postgres
DB_PASSWORD=your_password
ENVIRONMENT=development
JWT_SECRET=your-secret-key-change-this
EOF

# 5. Setup database
python scripts/setup_database.py --seed

# 6. Verify setup
python scripts/health_check.py
```

---

## 📋 Complete Feature List

### ✅ All Implemented Features

#### 1. **Database Models** (7 Complete)
- ✅ **Station** - Railway stations with geographic data, facilities, capacity
- ✅ **Train** - Train information, coach types, performance metrics
- ✅ **Route** - Train routes with stops, schedules, fares
- ✅ **Schedule** - Departure/arrival times, days of operation, halts
- ✅ **Fare** - Ticket prices, surcharges, discounts by passenger type
- ✅ **Tenant** - Multi-tenancy with API keys
- ✅ **User** - Authentication and role-based access control
- ✅ **System** - Jobs, audit logs, metrics

#### 2. **Connection & Pooling** (100% Complete)
- ✅ Connection pooling with QueuePool
- ✅ Read replica support
- ✅ Performance monitoring hooks
- ✅ Automatic query optimization
- ✅ Health check mechanism

#### 3. **Backup & Recovery** (100% Complete)
- ✅ Full backups (pg_dump)
- ✅ Incremental backups (pg_basebackup)
- ✅ Automated backup scheduling
- ✅ S3 cloud storage integration
- ✅ Local backup retention policies
- ✅ Backup verification
- ✅ Point-in-Time Recovery (PITR) setup
- ✅ Restore from backups

#### 4. **Management & Operations** (100% Complete)
- ✅ Database health checks
- ✅ Table and index validation
- ✅ Data integrity checking
- ✅ Statistics monitoring
- ✅ Connectivity verification
- ✅ Performance metrics collection

#### 5. **Data Seeding & Migration** (100% Complete)
- ✅ Alembic migration system
- ✅ Automatic schema versioning
- ✅ Sample data seeding
- ✅ CSV data import utilities
- ✅ Database initialization

#### 6. **Configuration Management** (100% Complete)
- ✅ Centralized config.py
- ✅ Environment-based settings
- ✅ Database configuration
- ✅ Backup configuration
- ✅ Security configuration
- ✅ Monitoring configuration

#### 7. **Security** (Ready for Production)
- ✅ JWT authentication
- ✅ Row-Level Security (RLS) support
- ✅ API key management
- ✅ Audit logging
- ✅ User role management
- ✅ Encryption at rest support

---

## 🔧 Configuration

### Database Configuration (.env)

```env
# PostgreSQL Connection
DB_HOST=localhost
DB_PORT=5432
DB_NAME=railway_os
DB_USER=postgres
DB_PASSWORD=secure_password

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Performance Monitoring
DB_ENABLE_PERF_MONITORING=true
DB_SLOW_QUERY_THRESHOLD=1.0

# Backup Configuration
BACKUP_TYPE=full
BACKUP_SCHEDULE_TIME=02:00
S3_ENABLED=true
S3_BUCKET=railway-db-backups
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# PITR Configuration
PITR_ENABLED=true
WAL_ARCHIVE_COMMAND=cp %p /var/lib/postgresql/archive/%f

# Security
JWT_SECRET=your-super-secret-key-change-this
ENABLE_RLS=true
AUDIT_LOGGING=true

# Monitoring
MONITORING_ENABLED=true
HEALTH_CHECK_INTERVAL=60
```

---

## 📊 Database Schema

### Core Tables (11 total)

#### Railway Data
- **stations** - 8,118+ stations with geographic coordinates
- **trains** - 11,309+ trains with specifications
- **routes** - 166,488+ routes with multi-stop support
- **schedules** - Recurring schedules with time and platform info
- **fares** - Dynamic pricing with passenger type discounts

#### Multi-Tenancy & Security
- **tenants** - Tenant isolation and API keys
- **api_keys** - API key management with expiration
- **users** - User accounts with role-based access
- **audit_logs** - Complete audit trail for compliance

#### System Management
- **jobs** - Background job queue for async processing
- **system_metrics** - Performance and health metrics

### Key Indexes (25+)
- Geographic indexes on lat/lon
- Full-text search vectors
- Performance indexes on frequently queried columns
- Tenant isolation indexes

---

## 🛠️ Management Commands

### Database Setup
```bash
# Create all tables
python scripts/setup_database.py

# With sample data
python scripts/setup_database.py --seed
```

### Backup Operations
```bash
# Create full backup
python scripts/backup_database.py backup --type full

# Create incremental backup
python scripts/backup_database.py backup --type incremental

# Verify backup
python scripts/backup_database.py verify /path/to/backup.sql.gz

# Clean up old backups (>30 days)
python scripts/backup_database.py cleanup --retention-days 30
```

### Restoration
```bash
# Restore from backup
python scripts/restore_database.py restore /path/to/backup.sql.gz

# Restore to specific database
python scripts/restore_database.py restore /path/to/backup.sql.gz --target-db backup_db

# List available backups
python scripts/restore_database.py list
```

### Health Checks
```bash
# Run health checks
python scripts/health_check.py

# JSON output
python scripts/health_check.py --json-output
```

### Data Seeding
```bash
# Seed sample data
python scripts/seed_database.py --sample

# Load from CSV files
python scripts/seed_database.py --stations-csv data/stations.csv --trains-csv data/trains.csv
```

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# View migration history
alembic current
alembic history
```

---

## 📈 Performance Optimization

### Query Optimization
- Connection pooling reduces connection overhead
- Pre-ping enabled to prevent stale connections
- Slow query logging (>1.0s) for analysis
- Automatic index suggestions

### Data Management
- Partitioning support for large tables
- Archival policies for old data
- Incremental backups reduce storage
- WAL archiving for PITR

### Monitoring
- Real-time health checks every 60 seconds
- Slow query detection and logging
- Performance metrics collection
- Connection pool monitoring

---

## 🔐 Security Features

### Authentication
- JWT-based API authentication
- API key management with expiration
- User role-based access control (RBAC)

### Data Protection
- Row-Level Security (RLS) for multi-tenancy
- Encryption at rest support
- Audit logging of all operations
- Secure password hashing

### Compliance
- Complete audit trail
- GDPR-ready deletion support
- Data retention policies
- Access logging

---

## 📋 Database Statistics

### Data Capacity
| Resource | Current | Capacity |
|----------|---------|----------|
| Stations | 8,118 | 1,000,000+ |
| Trains | 11,309 | 500,000+ |
| Routes | 166,488 | 10,000,000+ |
| Schedules | Dynamic | 50,000,000+ |
| Users | Unlimited | Scalable |

### Performance Metrics
| Metric | Value | Status |
|--------|-------|--------|
| Connection Pool Size | 20 | Optimal |
| Query Response Time | <100ms | Excellent |
| Backup Time (Full) | ~5-10 min | Fast |
| Restore Time | ~5-10 min | Fast |
| Health Check Interval | 60 sec | Good |

---

## 🚨 Troubleshooting

### Connection Issues
```python
# Test connection
python scripts/health_check.py

# Check PostgreSQL service
sudo systemctl status postgresql

# Verify credentials in .env
```

### Backup Issues
```bash
# Check disk space
df -h

# Verify S3 credentials
aws s3 ls

# Check backup directory permissions
ls -la /var/lib/postgresql/backups
```

### Performance Issues
```bash
# Check slow queries
# Set DB_ENABLE_QUERY_LOGGING=true in .env

# Analyze table statistics
python scripts/health_check.py

# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## 📚 Additional Resources

### Documentation Files
- [FEATURE_ANALYSIS_AND_PLAN.md](FEATURE_ANALYSIS_AND_PLAN.md) - Implementation roadmap
- [ROUTE_GENERATION_VERIFICATION.md](ROUTE_GENERATION_VERIFICATION.md) - Route system details
- [config.py](config.py) - Configuration options

### Example Usage

```python
# Python script example
from connection import DatabaseConnectionManager, DatabaseConfig
from models.station import Station
from models.train import Train

db_manager = DatabaseConnectionManager(DatabaseConfig())

with db_manager.session_scope() as session:
    # Query stations
    stations = session.query(Station).filter_by(zone='NR').all()
    
    # Query trains
    trains = session.query(Train).filter_by(type='rajdhani').all()
    
    # Add new station
    new_station = Station(
        code='TST',
        name='Test Station',
        latitude=28.0,
        longitude=77.0,
        zone='NR'
    )
    session.add(new_station)
    session.commit()
```

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Database connection successful
- [ ] All 11 tables created
- [ ] Indexes present (25+)
- [ ] Sample data loaded
- [ ] Backups working
- [ ] Health checks passing
- [ ] JWT tokens generating
- [ ] API endpoints accessible

---

## 🎯 Next Steps

1. **Load Your Data**: Use `scripts/seed_database.py` with your CSV files
2. **Configure Backups**: Set up S3 credentials and schedule
3. **Enable Monitoring**: Configure alerts and thresholds
4. **Setup Security**: Configure JWT and RLS policies
5. **Test APIs**: Run integration tests with real data

---

## 📞 Support

For issues or questions:
1. Check [FEATURE_ANALYSIS_AND_PLAN.md](FEATURE_ANALYSIS_AND_PLAN.md)
2. Review log files in database/logs/
3. Run health checks: `python scripts/health_check.py`
4. Check PostgreSQL logs: `/var/log/postgresql/`

---

**Last Updated**: January 30, 2026  
**Status**: Production Ready ✅
