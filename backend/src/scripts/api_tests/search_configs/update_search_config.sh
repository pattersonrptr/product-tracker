#!/bin/bash
# Update a search config
# Usage: ./update_search_config.sh [search_config_id] [search_term] [is_active] [frequency_days] [preferred_time]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

SEARCH_CONFIG_ID="${1:-1}"
SEARCH_TERM="${2:-updated laptop}"
IS_ACTIVE="${3:-true}"
FREQUENCY_DAYS="${4:-7}"
PREFERRED_TIME="${5:-09:00:00}"

curl -s -X PUT "$API_BASE_URL/search-configs/$SEARCH_CONFIG_ID" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "search_config",
      "attributes": {
        "search_term": "'"$SEARCH_TERM"'",
        "is_active": '"$IS_ACTIVE"',
        "frequency_days": '"$FREQUENCY_DAYS"',
        "preferred_time": "'"$PREFERRED_TIME"'"
      }
    }
  }' | python3 -m json.tool

echo ""
