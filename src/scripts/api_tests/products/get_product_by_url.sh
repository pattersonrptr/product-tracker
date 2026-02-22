#!/bin/bash
# Get a product by URL
# Usage: ./get_product_by_url.sh [url]

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

# Product URL (default to a test URL)
PRODUCT_URL="${1:-https://www.mercadolivre.com.br/test-product}"

# URL encode the product URL
ENCODED_URL=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PRODUCT_URL'))")

# Get product by URL
curl -s -X GET "$API_BASE_URL/products/url?url=$ENCODED_URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json" | python3 -m json.tool

echo ""
