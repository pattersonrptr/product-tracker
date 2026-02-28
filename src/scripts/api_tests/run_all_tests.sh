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
    # Source Website Tests
    # ========================================
    print_section "4. Source Website Tests"

    echo -e "${YELLOW}Creating a source website for testing...${NC}"
    SW_RESPONSE=$("$SCRIPT_DIR/source_websites/create_source_website.sh" 2>/dev/null)
    SW_ID=$(echo "$SW_RESPONSE" | grep '"id"' | head -1 | grep -o '[0-9]\+')

    if [ -z "$SW_ID" ]; then
        echo -e "${RED}Failed to create test source website${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created test source website with ID: $SW_ID${NC}\n"

    run_test "List Source Websites" "$SCRIPT_DIR/source_websites/list_source_websites.sh"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Source Website by ID ($SW_ID)"
    if bash "$SCRIPT_DIR/source_websites/get_source_website_by_id.sh" "$SW_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Update Source Website ($SW_ID)"
    if bash "$SCRIPT_DIR/source_websites/update_source_website.sh" "$SW_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Delete Source Website ($SW_ID)"
    if bash "$SCRIPT_DIR/source_websites/delete_source_website.sh" "$SW_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # ========================================
    # Price History Tests
    # ========================================
    print_section "5. Price History Tests"

    # We need a product for price history — create a source website first, then a product
    echo -e "${YELLOW}Creating a source website for price history testing...${NC}"
    PH_SW_RESPONSE=$("$SCRIPT_DIR/source_websites/create_source_website.sh" "PH Test Site" "https://ph-test.com.br" 2>/dev/null)
    PH_SW_ID=$(echo "$PH_SW_RESPONSE" | grep '"id"' | head -1 | grep -o '[0-9]\+')

    if [ -z "$PH_SW_ID" ]; then
        echo -e "${RED}Failed to create source website for price history test${NC}"
        exit 1
    fi

    echo -e "${YELLOW}Creating a product for price history testing...${NC}"
    PH_PRODUCT_RESPONSE=$("$SCRIPT_DIR/products/create_product.sh" "Price History Test Product" "" "$PH_SW_ID" 2>/dev/null)
    PH_PRODUCT_ID=$(echo "$PH_PRODUCT_RESPONSE" | grep '"id"' | head -1 | grep -o '[0-9]\+')

    if [ -z "$PH_PRODUCT_ID" ]; then
        echo -e "${RED}Failed to create product for price history test${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created test product with ID: $PH_PRODUCT_ID${NC}\n"

    echo -e "${YELLOW}Creating a price history record for testing...${NC}"
    PH_RESPONSE=$("$SCRIPT_DIR/price_histories/create_price_history.sh" "$PH_PRODUCT_ID" "499.90" 2>/dev/null)
    PH_ID=$(echo "$PH_RESPONSE" | grep '"id"' | head -1 | grep -o '[0-9]\+')

    if [ -z "$PH_ID" ]; then
        echo -e "${RED}Failed to create test price history${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created price history with ID: $PH_ID${NC}\n"

    run_test "List Price Histories" "$SCRIPT_DIR/price_histories/list_price_histories.sh"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Price History by ID ($PH_ID)"
    if bash "$SCRIPT_DIR/price_histories/get_price_history_by_id.sh" "$PH_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Price History by Product ID ($PH_PRODUCT_ID)"
    if bash "$SCRIPT_DIR/price_histories/get_price_history_by_product_id.sh" "$PH_PRODUCT_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Latest Price by Product ID ($PH_PRODUCT_ID)"
    if bash "$SCRIPT_DIR/price_histories/get_latest_price_by_product_id.sh" "$PH_PRODUCT_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Delete Price History ($PH_ID)"
    if bash "$SCRIPT_DIR/price_histories/delete_price_history.sh" "$PH_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # Cleanup: delete the product and source website created for price history tests
    bash "$SCRIPT_DIR/products/delete_product.sh" "$PH_PRODUCT_ID" > /dev/null 2>&1 || true
    bash "$SCRIPT_DIR/source_websites/delete_source_website.sh" "$PH_SW_ID" > /dev/null 2>&1 || true

    # ========================================
    # Search Config Tests
    # ========================================
    print_section "6. Search Config Tests"

    echo -e "${YELLOW}Creating a search config for testing...${NC}"
    SC_RESPONSE=$("$SCRIPT_DIR/search_configs/create_search_config.sh" "test laptop" "1" "1" 2>/dev/null)
    SC_ID=$(echo "$SC_RESPONSE" | grep '"id"' | head -1 | grep -o '[0-9]\+')

    if [ -z "$SC_ID" ]; then
        echo -e "${RED}Failed to create test search config${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Created search config with ID: $SC_ID${NC}\n"

    run_test "List Search Configs" "$SCRIPT_DIR/search_configs/list_search_configs.sh"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Search Config by ID ($SC_ID)"
    if bash "$SCRIPT_DIR/search_configs/get_search_config_by_id.sh" "$SC_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Get Search Configs by User ID (1)"
    if bash "$SCRIPT_DIR/search_configs/get_search_configs_by_user_id.sh" "1"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Update Search Config ($SC_ID)"
    if bash "$SCRIPT_DIR/search_configs/update_search_config.sh" "$SC_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    print_test "Delete Search Config ($SC_ID)"
    if bash "$SCRIPT_DIR/search_configs/delete_search_config.sh" "$SC_ID"; then
        echo -e "${GREEN}✓ PASSED${NC}\n"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}\n"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi

    # ========================================
    # Search Execution Log Tests (read-only)
    # ========================================
    print_section "7. Search Execution Log Tests (read-only)"

    run_test "List Search Execution Logs" "$SCRIPT_DIR/search_execution_logs/list_search_execution_logs.sh"
    run_test "Get Search Execution Logs by Search Config ID (1)" "$SCRIPT_DIR/search_execution_logs/get_search_execution_logs_by_search_config_id.sh"

    # ========================================
    # Summary
    # ========================================
    print_summary
}

# Run main function
main

# Exit with appropriate code
exit $FAILED_TESTS
