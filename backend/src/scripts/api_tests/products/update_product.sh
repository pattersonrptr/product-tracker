#!/bin/bash
# Update a product
# Usage: ./update_product.sh [product_id] [title] [price]

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

# Product data with defaults
PRODUCT_ID="${1:-1}"
TITLE="${2:-Updated Test Product}"
PRICE="${3:-299.99}"

# Update product request
curl -s -X PUT "$API_BASE_URL/products/$PRODUCT_ID" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "product",
      "attributes": {
        "title": "'"$TITLE"'",
        "price": '"$PRICE"',
        "description": "Updated product description",
        "availability": true
      }
    }
  }' | python3 -m json.tool

echo ""
