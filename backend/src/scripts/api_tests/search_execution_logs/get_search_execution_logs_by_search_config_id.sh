#!/bin/bash
# Get all search execution logs for a given search config
# Usage: ./get_search_execution_logs_by_search_config_id.sh [search_config_id]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

SEARCH_CONFIG_ID="${1:-1}"

curl -s -X GET "$API_BASE_URL/search-execution-logs/search-config/$SEARCH_CONFIG_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json" | python3 -m json.tool

echo ""
