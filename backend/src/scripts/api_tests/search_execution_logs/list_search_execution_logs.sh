#!/bin/bash
# List all search execution logs with pagination
# Usage: ./list_search_execution_logs.sh [limit] [offset] [sort_by] [sort_order]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

LIMIT="${1:-10}"
OFFSET="${2:-0}"
SORT_BY="${3:-started_at}"
SORT_ORDER="${4:-desc}"

curl -s -X GET "$API_BASE_URL/search-execution-logs/?limit=$LIMIT&offset=$OFFSET&sort_by=$SORT_BY&sort_order=$SORT_ORDER" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json" | python3 -m json.tool

echo ""
