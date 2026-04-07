#!/bin/bash
# POST /auth/login

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

curl -X POST "$API_BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
