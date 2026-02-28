#!/bin/bash
# Get all search configs for a user
# Usage: ./get_search_configs_by_user_id.sh [user_id]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

USER_ID="${1:-1}"

curl -s -X GET "$API_BASE_URL/search-configs/user/$USER_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json" | python3 -m json.tool

echo ""
