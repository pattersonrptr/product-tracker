#!/bin/bash
# List all products with pagination
# Usage: ./list_products.sh [limit] [offset] [sort_by] [sort_order]

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

# Query parameters with defaults
LIMIT="${1:-10}"
OFFSET="${2:-0}"
SORT_BY="${3:-created_at}"
SORT_ORDER="${4:-desc}"

# Build query string
QUERY="?limit=$LIMIT&offset=$OFFSET&sort_by=$SORT_BY&sort_order=$SORT_ORDER"

# List products
curl -s -X GET "$API_BASE_URL/products/$QUERY" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json" | python3 -m json.tool

echo ""
