#!/bin/bash

# Railway Operating System - Setup Script
# This script helps you set up the Railway Operating System microservices platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_success "Docker and Docker Compose are installed"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_success "Python $PYTHON_VERSION is installed"
    else
        print_error "Python 3.8+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
}

# Create environment file
setup_environment() {
    if [ ! -f ".env" ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env
        print_success ".env file created. Please edit it with your configuration."
        print_warning "Remember to update database passwords and other sensitive values!"
    else
        print_info ".env file already exists"
    fi
}

# Build and start services
start_services() {
    print_info "Building and starting services..."

    # Start infrastructure first
    print_info "Starting infrastructure services (PostgreSQL, Redis, RabbitMQ)..."
    docker-compose up -d postgres redis rabbitmq

    # Wait for database to be ready
    print_info "Waiting for PostgreSQL to be ready..."
    sleep 10

    # Initialize database
    print_info "Initializing database..."
    docker-compose exec -T postgres psql -U railway_user -d railway_os -f /docker-entrypoint-initdb.d/init-db.sql || true

    # Start all services
    print_info "Starting all services..."
    docker-compose up -d

    print_success "Services started successfully!"
}

# Check service health
check_health() {
    print_info "Checking service health..."

    services=("api-gateway" "auth-service" "route-service" "data-service" "worker-service")

    for service in "${services[@]}"; do
        print_info "Checking $service..."
        if docker-compose ps $service | grep -q "Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
        fi
    done
}

# Run tests
run_tests() {
    print_info "Running tests..."

    # Run tests for each service
    services=("auth-service" "route-service" "data-service")

    for service in "${services[@]}"; do
        print_info "Running tests for $service..."
        docker-compose exec $service python -m pytest tests/ -v || print_warning "Tests failed for $service"
    done
}

# Show usage information
show_usage() {
    echo "Railway Operating System - Setup Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initial setup (check dependencies, create .env)"
    echo "  start     - Build and start all services"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  logs      - Show logs from all services"
    echo "  health    - Check health of all services"
    echo "  test      - Run tests for all services"
    echo "  clean     - Remove all containers and volumes"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup    # Initial setup"
    echo "  $0 start    # Start the platform"
    echo "  $0 logs     # View logs"
}

# Main script logic
case "${1:-setup}" in
    "setup")
        print_info "Starting Railway Operating System setup..."
        check_docker
        check_python
        setup_environment
        print_success "Setup completed! Run '$0 start' to start the services."
        ;;
    "start")
        start_services
        sleep 5
        check_health
        ;;
    "stop")
        print_info "Stopping services..."
        docker-compose down
        print_success "Services stopped"
        ;;
    "restart")
        print_info "Restarting services..."
        docker-compose restart
        sleep 5
        check_health
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "health")
        check_health
        ;;
    "test")
        run_tests
        ;;
    "clean")
        print_warning "This will remove all containers, volumes, and data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup completed"
        fi
        ;;
    "help"|*)
        show_usage
        ;;
esac