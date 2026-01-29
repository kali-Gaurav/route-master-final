# Setup script for Docker volumes and directories (Windows)
# Run this before starting Docker Compose

Write-Host "Setting up Docker volumes and directories..." -ForegroundColor Green

# Create volume directories
$directories = @(
    "volumes\postgres",
    "volumes\redis",
    "logs",
    "cache",
    "backups",
    "reports",
    "data"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ Created: $dir" -ForegroundColor Cyan
    } else {
        Write-Host "✓ Exists: $dir" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✓ Directories created successfully" -ForegroundColor Green
Write-Host "✓ Ready to start Docker services" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Copy .env.example to .env and configure"
Write-Host "  2. Run: docker-compose up --build"
Write-Host "     or with make: make quick-start"
