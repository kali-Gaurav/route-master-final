# Database System Starter and Requirements

## Overview
The Database System provides PostgreSQL-based data storage with automated migrations, backup/restore capabilities, and retention policies. It supports multi-tenancy, high availability, and point-in-time recovery.

## Requirements

### System Requirements
- PostgreSQL 14+ (15 recommended)
- Python 3.10+ (for migration tools)
- AWS CLI (for S3 backups)
- pg_dump and pg_restore utilities

### Dependencies
```python
# requirements.txt
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
boto3==1.28.57
python-dotenv==1.0.0
click==8.1.7
schedule==1.2.1
```

## Techniques Used

### Database Engine
- **PostgreSQL 14+**: Advanced relational database with JSON support
- **SQLAlchemy ORM**: Python object-relational mapping
- **Alembic Migrations**: Version-controlled schema changes

### High Availability
- **Connection Pooling**: Efficient connection management
- **Read Replicas**: Optional read scaling (future enhancement)
- **Automated Backups**: Scheduled database dumps to S3

### Data Management
- **Multi-tenancy**: Schema-per-tenant or database-per-tenant options
- **Data Partitioning**: Time-based partitioning for large tables
- **Indexing Strategy**: Optimized indexes for query performance

### Backup & Recovery
- **Point-in-Time Recovery (PITR)**: Continuous archiving with WAL
- **Retention Policies**: Hot (30d), Warm (180d), Cold (365d) storage
- **Automated Restore**: One-command database restoration

### Monitoring & Maintenance
- **Health Checks**: Database connectivity and performance monitoring
- **Schema Drift Detection**: Automated comparison of actual vs expected schema
- **Query Optimization**: Index recommendations and slow query analysis

## Data Requirements

### Core Schema
The system requires the following database schema:

#### Tenancy Tables
```sql
-- Tenant management
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    schema_name VARCHAR(100) UNIQUE,
    database_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API key management
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    permissions JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Railway Data Tables
```sql
-- Stations
CREATE TABLE stations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    state VARCHAR(100),
    zone VARCHAR(50),
    platform_count INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trains
CREATE TABLE trains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    type VARCHAR(50) NOT NULL, -- passenger, freight, express
    operator VARCHAR(100),
    total_coaches INTEGER,
    max_speed_kmph INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Routes
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    train_id UUID NOT NULL REFERENCES trains(id),
    origin_station_id UUID NOT NULL REFERENCES stations(id),
    dest_station_id UUID NOT NULL REFERENCES stations(id),
    distance_km DECIMAL(10,2) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    stops JSONB, -- Array of stop stations with times
    days_of_operation INTEGER[], -- Bitmask for days (1=Monday, 2=Tuesday, etc.)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Schedules
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES routes(id),
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    platform VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fares
CREATE TABLE fares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES routes(id),
    class VARCHAR(20) NOT NULL, -- 1A, 2A, 3A, SL, etc.
    base_fare DECIMAL(10,2) NOT NULL,
    reservation_charge DECIMAL(8,2) DEFAULT 0,
    superfast_charge DECIMAL(8,2) DEFAULT 0,
    tatkal_charge DECIMAL(8,2) DEFAULT 0,
    effective_from DATE NOT NULL,
    effective_to DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### System Tables
```sql
-- Job processing
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 1,
    payload JSONB,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logging
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- System metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    labels JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Initial Data
The system requires initial seed data:

#### Stations Data
CSV format with columns: code,name,latitude,longitude,state,zone
Example:
```
NDLS,New Delhi,28.6415,77.2200,Delhi,NR
BCT,Mumbai Central,18.9690,72.8194,Maharashtra,WR
HWH,Howrah Junction,22.5832,88.3378,West Bengal,ER
```

#### Trains Data
CSV format with columns: number,name,type,operator
Example:
```
12951,Mumbai Rajdhani Express,Rajdhani,NR
12627,Karnataka Express,Superfast,SWR
```

### Configuration Data
```python
# config.py
class DatabaseConfig:
    # Connection settings
    host: str = "localhost"
    port: int = 5432
    database: str = "railway_db"
    username: str = "railway_user"
    password: str = "secure_password"
    
    # Pool settings
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    
    # Backup settings
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    s3_bucket: str = "railway-db-backups"
    s3_region: str = "us-east-1"
    
    # PITR settings
    wal_level: str = "replica"
    archive_mode: str = "on"
    archive_command: str = "cp %p /var/lib/postgresql/archive/%f"
    
    # Multi-tenancy
    tenancy_model: str = "schema"  # schema or database
```

## Setup and Installation

### 1. PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql
brew services start postgresql

# Windows
# Download from postgresql.org
```

### 2. Database Creation
```bash
# Create user and database
sudo -u postgres psql
CREATE USER railway_user WITH PASSWORD 'secure_password';
CREATE DATABASE railway_db OWNER railway_user;
GRANT ALL PRIVILEGES ON DATABASE railway_db TO railway_user;
\q
```

### 3. Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration
Create `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=railway_db
DB_USER=railway_user
DB_PASSWORD=secure_password
BACKUP_S3_BUCKET=railway-db-backups
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 5. Run Migrations
```bash
# Initialize Alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 6. Seed Initial Data
```bash
# Run data seeding script
python scripts/seed_database.py --stations data/stations.csv --trains data/trains.csv
```

### 7. Configure Backups
```bash
# Setup automated backups
python scripts/setup_backup.py

# Test backup
python scripts/backup_database.py

# Test restore
python scripts/restore_database.py --backup-id latest
```

### 8. PITR Setup (Optional)
```bash
# Configure WAL archiving
sudo -u postgres psql -d railway_db -c "ALTER SYSTEM SET wal_level = 'replica';"
sudo -u postgres psql -d railway_db -c "ALTER SYSTEM SET archive_mode = 'on';"
sudo -u postgres psql -d railway_db -c "ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';"

# Restart PostgreSQL
sudo systemctl restart postgresql

# Create base backup
pg_basebackup -D /var/lib/postgresql/backup/base -Ft -z -P
```

## Management Commands

### Database Operations
```bash
# Check database health
python -m database_system.health_check

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new table"

# Seed data
python scripts/seed_database.py
```

### Backup Operations
```bash
# Manual backup
python scripts/backup_database.py --type full

# List backups
python scripts/list_backups.py

# Restore from backup
python scripts/restore_database.py --backup-id 2024-01-28_02-00-00

# Cleanup old backups
python scripts/cleanup_backups.py --retention-days 30
```

### Monitoring
```bash
# Check schema drift
python scripts/check_schema_drift.py

# Analyze slow queries
python scripts/analyze_queries.py

# Generate performance report
python scripts/performance_report.py
```

## Integration Points

### With Backend
- Direct SQLAlchemy connections
- Connection pooling for high concurrency
- Transaction management for data consistency

### With Frontend
- Indirect access through backend APIs
- No direct frontend database connections

### With Deployment
- Environment-specific database configurations
- Automated backup integration with CI/CD
- Health check endpoints for load balancers

## Development Workflow

1. **Schema Design**: Use SQLAlchemy models for table definitions
2. **Migration Creation**: Generate Alembic migrations for schema changes
3. **Data Seeding**: Create scripts for initial and test data
4. **Backup Testing**: Regularly test backup and restore procedures
5. **Performance Monitoring**: Monitor query performance and optimize indexes
6. **Security**: Implement row-level security for multi-tenancy

## Key Files Structure
```
database_system/
├── alembic/               # Migration files
│   ├── versions/
│   └── env.py
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   ├── tenant.py
│   ├── station.py
│   ├── train.py
│   ├── route.py
│   └── audit.py
├── migrations/            # Custom migration scripts
│   ├── __init__.py
│   └── data_migration.py
├── backup/                # Backup utilities
│   ├── __init__.py
│   ├── s3_backup.py
│   └── restore.py
├── scripts/               # Management scripts
│   ├── setup_database.py
│   ├── seed_database.py
│   ├── backup_database.py
│   ├── restore_database.py
│   └── health_check.py
├── config.py              # Database configuration
├── connection.py          # Connection management
├── __init__.py
├── requirements.txt
└── README.md
```</content>
<parameter name="filePath">c:\Users\Gaurav Nagar\OneDrive\Documents\testingfolder_v3\railway-operating-system-microservices\database_starter.md