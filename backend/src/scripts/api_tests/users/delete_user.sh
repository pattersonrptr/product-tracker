#!/bin/bash
# DELETE /users/{user_id} - Delete user (requires superuser token)

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_ID="${1:-2}"

# Get token from login script
TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X DELETE "$API_BASE_URL/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
