#!/bin/bash
# Delete a product by ID
# Usage: ./delete_product.sh [product_id]

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# API configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

# Get authentication token
TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

# Product ID (default to 1)
PRODUCT_ID="${1:-1}"

# Delete product
curl -s -X DELETE "$API_BASE_URL/products/$PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json"

echo ""
echo "Product $PRODUCT_ID deleted successfully (if it existed)"
