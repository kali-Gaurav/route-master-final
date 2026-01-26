#!/bin/bash
# Quick Test Runner - Executes all tests in proper sequence

echo "=========================================="
echo "Route Master - Vercel Deployment Test Suite"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Function to run a test
run_test() {
    local test_name=$1
    local test_file=$2
    local description=$3
    
    echo ""
    echo -e "${YELLOW}[TEST $((PASSED + FAILED + 1))]${NC} $test_name"
    echo "Description: $description"
    echo "---"
    
    if python "$test_file" 2>&1 | tee /tmp/test_output.txt; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        echo "Last 20 lines of output:"
        tail -20 /tmp/test_output.txt
    fi
}

# Test 1: Deployment Validation
run_test \
    "Deployment Readiness Check" \
    "vercel_deployment_validator.py" \
    "Validates all requirements for Vercel deployment"

# Test 2: Route Generation
run_test \
    "Route Generation Test" \
    "test_route_generation_complete.py" \
    "Tests route generation with all three categories"

# Test 3: Comprehensive Suite
run_test \
    "Comprehensive Test Suite" \
    "test_comprehensive_vercel.py" \
    "Full test coverage with 10 test categories"

# Final Summary
echo ""
echo "=========================================="
echo "TEST EXECUTION SUMMARY"
echo "=========================================="
echo -e "Total Tests Run: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo "=========================================="

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - READY FOR DEPLOYMENT${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED - REVIEW OUTPUT ABOVE${NC}"
    exit 1
fi
