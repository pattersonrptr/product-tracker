#!/bin/bash
# Delete a search config by ID
# Usage: ./delete_search_config.sh [search_config_id]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

SEARCH_CONFIG_ID="${1:-1}"

curl -s -X DELETE "$API_BASE_URL/search-configs/$SEARCH_CONFIG_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json"

echo ""
echo "Search config $SEARCH_CONFIG_ID deleted successfully (if it existed)"
