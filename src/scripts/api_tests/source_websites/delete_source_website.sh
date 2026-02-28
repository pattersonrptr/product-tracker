#!/bin/bash
# Delete a source website by ID
# Usage: ./delete_source_website.sh [source_website_id]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

SOURCE_WEBSITE_ID="${1:-1}"

curl -s -X DELETE "$API_BASE_URL/source-websites/$SOURCE_WEBSITE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.api+json"

echo ""
echo "Source website $SOURCE_WEBSITE_ID deleted successfully (if it existed)"
