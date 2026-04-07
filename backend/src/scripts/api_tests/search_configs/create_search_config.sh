#!/bin/bash
# Create a new search config
# Usage: ./create_search_config.sh [search_term] [user_id] [frequency_days]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

SEARCH_TERM="${1:-laptop}"
USER_ID="${2:-1}"
FREQUENCY_DAYS="${3:-1}"

curl -s -X POST "$API_BASE_URL/search-configs/" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "search_config",
      "attributes": {
        "search_term": "'"$SEARCH_TERM"'",
        "user_id": '"$USER_ID"',
        "is_active": true,
        "frequency_days": '"$FREQUENCY_DAYS"',
        "preferred_time": "08:00:00",
        "source_website_ids": []
      }
    }
  }' | python3 -m json.tool

echo ""
