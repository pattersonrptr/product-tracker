#!/bin/bash
# POST /users - Create a new user (requires superuser token)

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get token from login script
TOKEN=$("$SCRIPT_DIR/../auth/login.sh" 2>/dev/null | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X POST "$API_BASE_URL/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "users",
      "attributes": {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "is_staff": false,
        "is_superuser": false
      }
    }
  }'
