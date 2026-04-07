#!/bin/bash
# POST /auth/verify-token

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

# Get token first
TOKEN=$(curl -s -X POST "$API_BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -X POST "$API_BASE_URL/auth/verify-token" \
  -H "Content-Type: application/vnd.api+json" \
  -d '{
    "data": {
      "type": "token-validation",
      "attributes": {
        "token": "'"$TOKEN"'"
      }
    }
  }'
