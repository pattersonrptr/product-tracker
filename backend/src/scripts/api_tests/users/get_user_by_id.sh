#!/bin/bash
# GET /users/{user_id} - Get user by ID (requires authentication)

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_ID="${1:-1}"

# Get token from login script
TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X GET "$API_BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
