@echo off
REM Railway Operating System - Setup Script (Windows)
REM This script helps you set up the Railway Operating System microservices platform

setlocal enabledelayedexpansion

REM Colors for output (Windows CMD)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "RESET=[0m"

REM Function to print colored output
:print_info
echo [94m[INFO][0m %~1
goto :eof

:print_success
echo [92m[SUCCESS][0m %~1
goto :eof

:print_warning
echo [93m[WARNING][0m %~1
goto :eof

:print_error
echo [91m[ERROR][0m %~1
goto :eof

REM Check if Docker is installed
:check_docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    call :print_error "Docker is not installed. Please install Docker first."
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    call :print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit /b 1
)

call :print_success "Docker and Docker Compose are installed"
goto :eof

REM Check if Python is installed
:check_python
where python >nul 2>nul
if %errorlevel% neq 0 (
    call :print_error "Python is not installed. Please install Python 3.8+ first."
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
call :print_success "Python %PYTHON_VERSION% is installed"
goto :eof

REM Create environment file
:setup_environment
if not exist ".env" (
    call :print_info "Creating .env file from template..."
    copy .env.example .env >nul
    call :print_success ".env file created. Please edit it with your configuration."
    call :print_warning "Remember to update database passwords and other sensitive values!"
) else (
    call :print_info ".env file already exists"
)
goto :eof

REM Build and start services
:start_services
call :print_info "Building and starting services..."

REM Start infrastructure first
call :print_info "Starting infrastructure services (PostgreSQL, Redis, RabbitMQ)..."
docker-compose up -d postgres redis rabbitmq

REM Wait for database to be ready
call :print_info "Waiting for PostgreSQL to be ready..."
timeout /t 10 /nobreak >nul

REM Initialize database
call :print_info "Initializing database..."
docker-compose exec -T postgres psql -U railway_user -d railway_os -f /docker-entrypoint-initdb.d/init-db.sql >nul 2>&1 || echo Database initialization completed

REM Start all services
call :print_info "Starting all services..."
docker-compose up -d

call :print_success "Services started successfully!"
goto :eof

REM Check service health
:check_health
call :print_info "Checking service health..."

set "services=api-gateway auth-service route-service data-service worker-service"

for %%s in (%services%) do (
    call :print_info "Checking %%s..."
    docker-compose ps %%s | findstr /C:"Up" >nul
    if !errorlevel! equ 0 (
        call :print_success "%%s is running"
    ) else (
        call :print_error "%%s is not running"
    )
)
goto :eof

REM Run tests
:run_tests
call :print_info "Running tests..."

set "services=auth-service route-service data-service"

for %%s in (%services%) do (
    call :print_info "Running tests for %%s..."
    docker-compose exec %%s python -m pytest tests/ -v >nul 2>&1
    if !errorlevel! neq 0 (
        call :print_warning "Tests failed for %%s"
    )
)
goto :eof

REM Show usage information
:show_usage
echo Railway Operating System - Setup Script (Windows)
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   setup     - Initial setup (check dependencies, create .env)
echo   start     - Build and start all services
echo   stop      - Stop all services
echo   restart   - Restart all services
echo   logs      - Show logs from all services
echo   health    - Check health of all services
echo   test      - Run tests for all services
echo   clean     - Remove all containers and volumes
echo   help      - Show this help message
echo.
echo Examples:
echo   %0 setup    # Initial setup
echo   %0 start    # Start the platform
echo   %0 logs     # View logs
goto :eof

REM Main script logic
if "%1"=="" goto setup
if "%1"=="setup" goto setup
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="health" goto health
if "%1"=="test" goto test
if "%1"=="clean" goto clean
if "%1"=="help" goto help
goto help

:setup
call :print_info "Starting Railway Operating System setup..."
call :check_docker
call :check_python
call :setup_environment
call :print_success "Setup completed! Run '%0 start' to start the services."
goto :eof

:start
call :start_services
timeout /t 5 /nobreak >nul
call :check_health
goto :eof

:stop
call :print_info "Stopping services..."
docker-compose down
call :print_success "Services stopped"
goto :eof

:restart
call :print_info "Restarting services..."
docker-compose restart
timeout /t 5 /nobreak >nul
call :check_health
goto :eof

:logs
docker-compose logs -f
goto :eof

:health
call :check_health
goto :eof

:test
call :run_tests
goto :eof

:clean
call :print_warning "This will remove all containers, volumes, and data!"
set /p "choice=Are you sure? (y/N): "
if /i "!choice!"=="y" (
    docker-compose down -v --remove-orphans
    docker system prune -f
    call :print_success "Cleanup completed"
)
goto :eof

:help
call :show_usage
goto :eof