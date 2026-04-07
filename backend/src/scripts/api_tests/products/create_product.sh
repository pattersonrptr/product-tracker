#!/bin/bash
# Create a new product
# Usage: ./create_product.sh [title] [url] [source_website_id]

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
TITLE="${1:-Test Product}"
URL="${2:-https://www.mercadolivre.com.br/test-product-$(date +%s)}"
SOURCE_WEBSITE_ID="${3:-1}"

# Create product request
curl -s -X POST "$API_BASE_URL/products/" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "product",
      "attributes": {
        "url": "'"$URL"'",
        "title": "'"$TITLE"'",
        "description": "Test product created via API script",
        "price": 199.99,
        "currency": "BRL",
        "condition": "new",
        "location": "São Paulo, SP",
        "seller_name": "Test Seller",
        "seller_rating": 4.5,
        "availability": true,
        "source_website_id": '"$SOURCE_WEBSITE_ID"',
        "source_product_code": "TEST-'$(date +%s)'",
        "source_metadata": {"test": true}
      }
    }
  }' | python3 -m json.tool

echo ""
