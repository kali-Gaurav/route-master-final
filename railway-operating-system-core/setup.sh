# Setup script for Docker volumes and permissions
# Run this before starting Docker Compose

echo "Setting up Docker volumes and directories..."

# Create volume directories
mkdir -p volumes/postgres
mkdir -p volumes/redis
mkdir -p logs
mkdir -p cache
mkdir -p backups
mkdir -p reports
mkdir -p data

# Set permissions (Unix-like systems)
if [ "$(uname)" != "Windows_NT" ]; then
    chmod -R 755 volumes
    chmod -R 755 logs
    chmod -R 755 cache
    chmod -R 755 backups
    chmod -R 755 reports
fi

echo "✓ Directories created successfully"
echo "✓ Ready to start Docker services"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and configure"
echo "  2. Run: make quick-start"
echo "     or: docker-compose up --build"
