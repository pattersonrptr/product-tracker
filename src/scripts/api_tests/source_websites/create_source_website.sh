#!/bin/bash
# Create a new source website
# Usage: ./create_source_website.sh [name] [base_url]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

NAME="${1:-Test Website $(date +%s)}"
BASE_URL="${2:-https://www.testwebsite-$(date +%s).com.br}"

curl -s -X POST "$API_BASE_URL/source-websites/" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "data": {
      "type": "source_website",
      "attributes": {
        "name": "'"$NAME"'",
        "base_url": "'"$BASE_URL"'",
        "is_active": true
      }
    }
  }' | python3 -m json.tool

echo ""
