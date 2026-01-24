#!/bin/bash
# Startup script for Route Master application
# Starts both backend and frontend servers

echo "========================================"
echo "Route Master - Startup Script"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Route Master Application...${NC}"
echo ""

# Check Python
echo "Checking Python installation..."
python --version
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python found${NC}"
else
    echo "✗ Python not found. Please install Python 3.8+"
    exit 1
fi

# Check Node
echo ""
echo "Checking Node installation..."
node --version
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Node found${NC}"
else
    echo "✗ Node not found. Please install Node.js"
    exit 1
fi

# Install dependencies
echo ""
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt
npm install

# Start backend
echo ""
echo -e "${BLUE}Starting Backend (Port 5000)...${NC}"
python api.py &
BACKEND_PID=$!

sleep 2

# Start frontend
echo -e "${BLUE}Starting Frontend (Port 5173)...${NC}"
npm run dev &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}========================================"
echo "Services Started Successfully!"
echo "========================================"
echo ""
echo -e "${BLUE}Frontend:${NC} http://localhost:5173"
echo -e "${BLUE}Backend:${NC} http://localhost:5000"
echo -e "${BLUE}API Docs:${NC} Check SETUP_AND_INTEGRATION.md"
echo ""
echo "Press Ctrl+C to stop all services"
echo "========================================"

# Wait for signals
wait
