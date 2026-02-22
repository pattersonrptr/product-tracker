#!/bin/bash
# Master script to run all API tests in correct order
# Usage: ./run_all_tests.sh [API_BASE_URL]
#
# This script runs all bash API tests sequentially, respecting dependencies.
# Tests are grouped by module and executed in order.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${1:-${API_BASE_URL:-http://localhost:8000}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Export for child scripts
export API_BASE_URL

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to print section header
print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to print test header
print_test() {
    echo -e "${YELLOW}▶ Running: $1${NC}"
}

# Function to run a test script
run_test() {
    local test_name="$1"
    local test_script="$2"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "$test_name"

    if bash "$test_script"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Function to print summary
print_summary() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  TEST SUMMARY${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo -e "Total Tests:  ${TOTAL_TESTS}"
    echo -e "Passed:       ${GREEN}${PASSED_TESTS}${NC}"
    echo -e "Failed:       ${RED}${FAILED_TESTS}${NC}"
    echo ""

    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         API Integration Tests Runner              ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "API Base URL: ${BLUE}$API_BASE_URL${NC}"
    echo -e "Test Directory: ${BLUE}$SCRIPT_DIR${NC}"
    echo ""

    # Check if API is reachable
    echo -e "${YELLOW}Checking API availability...${NC}"
    if ! curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/docs" | grep -q "200"; then
        echo -e "${RED}❌ Error: API is not reachable at $API_BASE_URL${NC}"
        echo -e "${YELLOW}Make sure the API is running with: docker compose up${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ API is reachable${NC}"

    # ========================================
    # Authentication Tests
    # ========================================
    print_section "1. Authentication Tests"

    run_test "Login" "$SCRIPT_DIR/auth/login.sh"
    run_test "Verify Token" "$SCRIPT_DIR/auth/verify_token.sh"
    run_test "Refresh Token" "$SCRIPT_DIR/auth/refresh_token.sh"

    # ========================================
    # User Management Tests
    # ========================================
    print_section "2. User Management Tests"

    run_test "List Users" "$SCRIPT_DIR/users/list_users.sh"
    run_test "Get User by ID" "$SCRIPT_DIR/users/get_user_by_id.sh"
    run_test "Get User by Username" "$SCRIPT_DIR/users/get_user_by_username.sh"
    run_test "Get User by Email" "$SCRIPT_DIR/users/get_user_by_email.sh"
    run_test "Create User" "$SCRIPT_DIR/users/create_user.sh"
    run_test "Update User" "$SCRIPT_DIR/users/update_user.sh"
    run_test "Delete User" "$SCRIPT_DIR/users/delete_user.sh"

    # ========================================
    # Product Management Tests
    # ========================================
    print_section "3. Product Management Tests"

    # Store the product ID from creation for later use
    echo -e "${YELLOW}Creating a product for testing...${NC}"
    PRODUCT_RESPONSE=$("$SCRIPT_DIR/products/create_product.sh" 2>/dev/null)
    PRODUCT_ID=$(echo "$PRODUCT_RESPONSE" | grep '"id"' | head -1 | grep -o '[0-9]\+')
    PRODUCT_URL=$(echo "$PRODUCT_RESPONSE" | grep '"url"' | head -1 | sed 's/.*"url": "\([^"]*\)".*/\1/')

    if [ -z "$PRODUCT_ID" ]; then
        echo -e "${RED}Failed to create test product${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created test product with ID: $PRODUCT_ID${NC}\n"

    run_test "List Products" "$SCRIPT_DIR/products/list_products.sh"

    # Use the created product ID for these tests
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Product by ID ($PRODUCT_ID)"
    if bash "$SCRIPT_DIR/products/get_product_by_id.sh" "$PRODUCT_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Product by URL"
    if bash "$SCRIPT_DIR/products/get_product_by_url.sh" "$PRODUCT_URL"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Update Product ($PRODUCT_ID)"
    if bash "$SCRIPT_DIR/products/update_product.sh" "$PRODUCT_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Delete Product ($PRODUCT_ID)"
    if bash "$SCRIPT_DIR/products/delete_product.sh" "$PRODUCT_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # ========================================
    # Summary
    # ========================================
    print_summary
}

# Run main function
main

# Exit with appropriate code
exit $FAILED_TESTS
