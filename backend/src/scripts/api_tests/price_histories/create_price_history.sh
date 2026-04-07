#!/bin/bash
# Create a new price history record for a product
# Usage: ./create_price_history.sh [product_id] [price]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

PRODUCT_ID="${1:-1}"
PRICE="${2:-199.99}"

curl -s -X POST "$API_BASE_URL/price-histories/" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "price_history",
      "attributes": {
        "product_id": '"$PRODUCT_ID"',
        "price": '"$PRICE"'
      }
    }
  }' | python3 -m json.tool

echo ""
