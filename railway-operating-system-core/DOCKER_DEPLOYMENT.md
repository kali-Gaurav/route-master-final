# 🐳 Docker Deployment Guide

## Railway Operating System - Containerized Deployment

This guide covers Docker-based deployment of the Railway Operating System with all services containerized following industry best practices.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Architecture](#architecture)
4. [Configuration](#configuration)
5. [Development](#development)
6. [Production](#production)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker Engine** 20.10+ ([Install Guide](https://docs.docker.com/engine/install/))
- **Docker Compose** 2.0+ ([Install Guide](https://docs.docker.com/compose/install/))
- **Git** (for cloning repository)
- **Make** (optional, for using Makefile commands)

### System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB free space

**Recommended:**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB free space

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd railway-operating-system-core
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Important:** Change default passwords and secrets in `.env`!

### 3. Start Services

#### Option A: Using Make (Recommended)

```bash
# Development environment with hot-reload
make dev

# Production environment
make prod
```

#### Option B: Using Docker Compose

```bash
# Development
docker-compose -f docker-compose.dev.yml up --build

# Production
docker-compose -f docker-compose.prod.yml.new up -d --build
```

### 4. Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **PgAdmin (dev):** http://localhost:5050

---

## 🏗️ Architecture

### Service Overview

```
┌─────────────────────────────────────────────┐
│           Load Balancer (Optional)          │
└─────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│    Frontend    │    │     Backend     │
│  (React/Vite)  │    │    (FastAPI)    │
│   Port: 3000   │    │   Port: 8000    │
└────────────────┘    └────────┬────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
           ┌────────▼────────┐   ┌───────▼────────┐
           │   PostgreSQL    │   │     Redis      │
           │   Port: 5432    │   │   Port: 6379   │
           └─────────────────┘   └────────────────┘
```

### Container Details

| Service    | Image                  | Purpose                    |
|------------|------------------------|----------------------------|
| Frontend   | node:18-alpine + nginx | React UI                   |
| Backend    | python:3.11-slim       | FastAPI application        |
| PostgreSQL | postgres:15-alpine     | Primary database           |
| Redis      | redis:7-alpine         | Cache and session storage  |
| Migrate    | python:3.11-slim       | Database migrations        |

---

## ⚙️ Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Security (CHANGE THESE!)
JWT_SECRET=<generate-with-openssl-rand-hex-32>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>

# Database
POSTGRES_DB=railway_db
POSTGRES_USER=railway_user

# Application
ENVIRONMENT=production
DEBUG=false
WORKERS=4
```

### Generate Secure Keys

```bash
# Generate JWT secret
openssl rand -hex 32

# Generate other secrets
openssl rand -base64 32
```

---

## 💻 Development

### Start Development Environment

```bash
# With hot-reload enabled
make dev

# Or manually
docker-compose -f docker-compose.dev.yml up
```

### Development Features

✅ **Hot Reload** - Code changes reflect immediately
✅ **Debug Mode** - Detailed error messages
✅ **Volume Mounts** - Edit code without rebuilding
✅ **Development Tools** - PgAdmin, Redis Commander

### Development Commands

```bash
# View logs
make dev-logs

# Run tests
make test

# Access backend shell
make shell-backend

# Access database
make db-shell

# Stop development
make dev-down
```

---

## 🚀 Production

### Production Deployment

```bash
# Start production services
make prod

# Or manually
docker-compose -f docker-compose.prod.yml.new up -d --build
```

### Production Features

✅ **Multi-stage Builds** - Optimized image sizes
✅ **Non-root Users** - Enhanced security
✅ **Health Checks** - Automatic service monitoring
✅ **Resource Limits** - Controlled resource usage
✅ **Restart Policies** - Automatic recovery

### Production Best Practices

1. **Use HTTPS** - Set up reverse proxy (Nginx/Traefik)
2. **Change Secrets** - Never use default passwords
3. **Enable Backups** - Regular database backups
4. **Monitor Resources** - Use `make stats`
5. **Update Regularly** - Keep images updated

---

## 🔧 Maintenance

### Database Backup

```bash
# Create backup
make db-backup

# Restore from backup
make db-restore FILE=backups/backup_20260130.sql
```

### Update Services

```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
make restart
```

### View Logs

```bash
# All services
make logs

# Specific service
make logs-backend
make logs-frontend
make logs-postgres
```

### Health Check

```bash
# Check service health
make health

# View detailed status
make status

# Resource usage
make stats
```

---

## 🧹 Cleanup

### Cleanup Commands

```bash
# Stop and remove containers
make down

# Remove containers and volumes
make clean

# Complete cleanup (including images)
make clean-all

# Prune unused resources
make prune-all
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8000   # Windows
lsof -i :8000                  # Linux/Mac

# Change port in .env
BACKEND_PORT=8001
```

#### 2. Database Connection Failed

```bash
# Check database status
docker-compose ps postgres

# View database logs
make logs-postgres

# Verify credentials in .env
```

#### 3. Frontend Can't Connect to Backend

```bash
# Check CORS settings in .env
ALLOWED_ORIGINS=http://localhost:3000

# Verify backend is running
curl http://localhost:8000/health
```

#### 4. Out of Disk Space

```bash
# Clean up unused resources
make prune-all

# Check disk usage
docker system df
```

#### 5. Container Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Rebuild without cache
make build-no-cache

# Fresh start
make fresh-start
```

---

## 📊 Monitoring

### Built-in Health Checks

All services include health checks:

```bash
# Check health status
docker-compose ps

# Services marked as "healthy" are operational
```

### Resource Monitoring

```bash
# Real-time resource usage
make stats

# Container inspection
docker inspect <container-name>
```

---

## 🔒 Security

### Security Best Practices

1. ✅ Run as non-root users
2. ✅ Use secrets management (not in code)
3. ✅ Keep images updated
4. ✅ Scan for vulnerabilities
5. ✅ Use HTTPS in production
6. ✅ Implement network policies

### Vulnerability Scanning

```bash
# Scan images (requires Trivy)
make scan

# Install Trivy
# Mac: brew install trivy
# Linux: See https://github.com/aquasecurity/trivy
```

---

## 📝 Additional Commands

### Makefile Commands Summary

```bash
make help           # Show all available commands
make dev            # Start development environment
make prod           # Start production environment
make build          # Build all images
make up             # Start services
make down           # Stop services
make logs           # View logs
make test           # Run tests
make migrate        # Run migrations
make clean          # Cleanup
make quick-start    # Quick start everything
```

---

## 🆘 Support

### Getting Help

1. Check logs: `make logs`
2. Review configuration: `.env` file
3. Verify Docker: `docker version`
4. Check resources: `make stats`

### Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

---

## 📄 License

See main README.md for license information.

---

**Ready to deploy?** Start with `make quick-start` for a complete setup!
