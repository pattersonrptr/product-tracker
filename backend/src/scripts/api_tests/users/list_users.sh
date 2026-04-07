#!/bin/bash
# GET /users - List all users (requires authentication)

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get token from login script
TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X GET "$API_BASE_URL/users/" \
  -H "Authorization: Bearer $TOKEN"
