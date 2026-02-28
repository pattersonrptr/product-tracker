#!/bin/bash
# Update a source website
# Usage: ./update_source_website.sh [source_website_id] [name] [is_active]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

SOURCE_WEBSITE_ID="${1:-1}"
NAME="${2:-Updated Website}"
IS_ACTIVE="${3:-true}"

curl -s -X PUT "$API_BASE_URL/source-websites/$SOURCE_WEBSITE_ID" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "source_website",
      "attributes": {
        "name": "'"$NAME"'",
        "is_active": '"$IS_ACTIVE"'
      }
    }
  }' | python3 -m json.tool

echo ""
