#!/bin/bash

# Railway Operating System - Testing Script
# This script runs comprehensive tests for the microservices platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_GATEWAY_URL="${API_GATEWAY_URL:-http://localhost:8000}"
TEST_TENANT_ID="test-tenant-001"
TEST_API_KEY="test-api-key-12345"

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

# Function to make HTTP requests
make_request() {
    local method=$1
    local url=$2
    local data=$3
    local headers=$4

    if [ "$method" = "GET" ]; then
        curl -s -X GET "$url" -H "Content-Type: application/json" $headers
    elif [ "$method" = "POST" ]; then
        curl -s -X POST "$url" -H "Content-Type: application/json" $headers -d "$data"
    elif [ "$method" = "PUT" ]; then
        curl -s -X PUT "$url" -H "Content-Type: application/json" $headers -d "$data"
    elif [ "$method" = "DELETE" ]; then
        curl -s -X DELETE "$url" -H "Content-Type: application/json" $headers
    fi
}

# Test health endpoints
test_health_endpoints() {
    print_info "Testing health endpoints..."

    local services=("api-gateway" "auth-service" "route-service" "data-service" "worker-service")

    for service in "${services[@]}"; do
        local health_url="${API_GATEWAY_URL}/health/${service}"
        local response=$(make_request "GET" "$health_url")

        if echo "$response" | grep -q '"status":"healthy"'; then
            print_success "$service health check passed"
        else
            print_error "$service health check failed: $response"
            return 1
        fi
    done
}

# Test tenant creation
test_tenant_creation() {
    print_info "Testing tenant creation..."

    local create_tenant_url="${API_GATEWAY_URL}/api/v1/tenants"
    local tenant_data='{
        "name": "Test Railway Company",
        "domain": "test-railway.com",
        "contact_email": "admin@test-railway.com",
        "settings": {
            "max_routes_per_request": 50,
            "cache_ttl": 3600
        }
    }'

    local response=$(make_request "POST" "$create_tenant_url" "$tenant_data")

    if echo "$response" | grep -q '"id"'; then
        TEST_TENANT_ID=$(echo "$response" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
        print_success "Tenant created successfully: $TEST_TENANT_ID"
    else
        print_error "Tenant creation failed: $response"
        return 1
    fi
}

# Test API key creation
test_api_key_creation() {
    print_info "Testing API key creation..."

    local create_key_url="${API_GATEWAY_URL}/api/v1/tenants/${TEST_TENANT_ID}/api-keys"
    local key_data='{
        "name": "Test API Key",
        "permissions": ["read:routes", "write:routes"],
        "expires_at": "2025-12-31T23:59:59Z"
    }'

    local response=$(make_request "POST" "$create_key_url" "$key_data")

    if echo "$response" | grep -q '"key"'; then
        TEST_API_KEY=$(echo "$response" | grep -o '"key":"[^"]*"' | cut -d'"' -f4)
        print_success "API key created successfully"
    else
        print_error "API key creation failed: $response"
        return 1
    fi
}

# Test route search
test_route_search() {
    print_info "Testing route search..."

    local search_url="${API_GATEWAY_URL}/api/v1/routes/search"
    local search_data='{
        "origin": "Delhi",
        "destination": "Mumbai",
        "date": "2024-01-15",
        "max_transfers": 2
    }'
    local headers="-H \"X-API-Key: ${TEST_API_KEY}\" -H \"X-Tenant-ID: ${TEST_TENANT_ID}\""

    local response=$(make_request "POST" "$search_url" "$search_data" "$headers")

    if echo "$response" | grep -q '"routes"'; then
        print_success "Route search successful"
    else
        print_error "Route search failed: $response"
        return 1
    fi
}

# Test data service
test_data_service() {
    print_info "Testing data service..."

    local stations_url="${API_GATEWAY_URL}/api/v1/stations"
    local headers="-H \"X-API-Key: ${TEST_API_KEY}\" -H \"X-Tenant-ID: ${TEST_TENANT_ID}\""

    local response=$(make_request "GET" "$stations_url" "" "$headers")

    if echo "$response" | grep -q '"stations"'; then
        print_success "Data service query successful"
    else
        print_error "Data service query failed: $response"
        return 1
    fi
}

# Test async job processing
test_async_processing() {
    print_info "Testing async job processing..."

    local async_search_url="${API_GATEWAY_URL}/api/v1/routes/search-async"
    local search_data='{
        "origin": "Chennai",
        "destination": "Kolkata",
        "date": "2024-01-15",
        "max_transfers": 3
    }'
    local headers="-H \"X-API-Key: ${TEST_API_KEY}\" -H \"X-Tenant-ID: ${TEST_TENANT_ID}\""

    local response=$(make_request "POST" "$async_search_url" "$search_data" "$headers")

    if echo "$response" | grep -q '"job_id"'; then
        local job_id=$(echo "$response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
        print_success "Async job created: $job_id"

        # Wait a bit and check job status
        sleep 5
        local status_url="${API_GATEWAY_URL}/api/v1/jobs/${job_id}/status"
        local status_response=$(make_request "GET" "$status_url" "" "$headers")

        if echo "$status_response" | grep -q '"status"'; then
            print_success "Job status check successful"
        else
            print_warning "Job status check returned: $status_response"
        fi
    else
        print_error "Async job creation failed: $response"
        return 1
    fi
}

# Test rate limiting
test_rate_limiting() {
    print_info "Testing rate limiting..."

    local test_url="${API_GATEWAY_URL}/api/v1/stations"
    local headers="-H \"X-API-Key: ${TEST_API_KEY}\" -H \"X-Tenant-ID: ${TEST_TENANT_ID}\""

    # Make multiple requests quickly
    local success_count=0
    local rate_limit_count=0

    for i in {1..15}; do
        local response=$(make_request "GET" "$test_url" "" "$headers")
        if echo "$response" | grep -q '"stations"'; then
            ((success_count++))
        elif echo "$response" | grep -q "429"; then
            ((rate_limit_count++))
        fi
        sleep 0.1
    done

    if [ $rate_limit_count -gt 0 ]; then
        print_success "Rate limiting working (success: $success_count, limited: $rate_limit_count)"
    else
        print_warning "Rate limiting may not be working properly"
    fi
}

# Test error handling
test_error_handling() {
    print_info "Testing error handling..."

    # Test invalid API key
    local invalid_headers="-H \"X-API-Key: invalid-key\" -H \"X-Tenant-ID: ${TEST_TENANT_ID}\""
    local response=$(make_request "GET" "${API_GATEWAY_URL}/api/v1/stations" "" "$invalid_headers")

    if echo "$response" | grep -q "401"; then
        print_success "Invalid API key properly rejected"
    else
        print_error "Invalid API key not properly rejected: $response"
    fi

    # Test invalid tenant
    local invalid_tenant_headers="-H \"X-API-Key: ${TEST_API_KEY}\" -H \"X-Tenant-ID: invalid-tenant\""
    local response=$(make_request "GET" "${API_GATEWAY_URL}/api/v1/stations" "" "$invalid_tenant_headers")

    if echo "$response" | grep -q "403"; then
        print_success "Invalid tenant properly rejected"
    else
        print_error "Invalid tenant not properly rejected: $response"
    fi
}

# Run performance tests
run_performance_tests() {
    print_info "Running performance tests..."

    local test_url="${API_GATEWAY_URL}/api/v1/stations"
    local headers="-H \"X-API-Key: ${TEST_API_KEY}\" -H \"X-Tenant-ID: ${TEST_TENANT_ID}\""

    print_info "Running 50 concurrent requests..."
    local start_time=$(date +%s.%3N)

    # Run 50 requests in parallel
    for i in {1..50}; do
        make_request "GET" "$test_url" "" "$headers" &
    done
    wait

    local end_time=$(date +%s.%3N)
    local duration=$(echo "$end_time - $start_time" | bc)

    print_success "Performance test completed in ${duration}s"
}

# Main test execution
main() {
    print_info "Starting Railway Operating System comprehensive tests..."
    print_info "API Gateway URL: $API_GATEWAY_URL"

    local test_results=()

    # Run all tests
    test_health_endpoints && test_results+=("health_endpoints:PASS") || test_results+=("health_endpoints:FAIL")
    test_tenant_creation && test_results+=("tenant_creation:PASS") || test_results+=("tenant_creation:FAIL")
    test_api_key_creation && test_results+=("api_key_creation:PASS") || test_results+=("api_key_creation:FAIL")
    test_route_search && test_results+=("route_search:PASS") || test_results+=("route_search:FAIL")
    test_data_service && test_results+=("data_service:PASS") || test_results+=("data_service:FAIL")
    test_async_processing && test_results+=("async_processing:PASS") || test_results+=("async_processing:FAIL")
    test_rate_limiting && test_results+=("rate_limiting:PASS") || test_results+=("rate_limiting:FAIL")
    test_error_handling && test_results+=("error_handling:PASS") || test_results+=("error_handling:FAIL")

    # Performance test (optional)
    if [ "${RUN_PERFORMANCE_TESTS:-false}" = "true" ]; then
        run_performance_tests && test_results+=("performance:PASS") || test_results+=("performance:FAIL")
    fi

    # Print results
    echo
    print_info "=== TEST RESULTS ==="
    local passed=0
    local failed=0

    for result in "${test_results[@]}"; do
        local test_name=$(echo "$result" | cut -d: -f1)
        local status=$(echo "$result" | cut -d: -f2)

        if [ "$status" = "PASS" ]; then
            print_success "$test_name: PASSED"
            ((passed++))
        else
            print_error "$test_name: FAILED"
            ((failed++))
        fi
    done

    echo
    print_info "Summary: $passed passed, $failed failed"

    if [ $failed -eq 0 ]; then
        print_success "All tests passed! 🎉"
        exit 0
    else
        print_error "Some tests failed. Please check the output above."
        exit 1
    fi
}

# Run main function
main "$@"