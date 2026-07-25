#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
sleep 2

echo -e "\n=== 1. Register User ==="
REG_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "finaluser", "email": "final@example.com", "password": "password123"}')
echo $REG_RESPONSE

echo -e "\n=== 2. Duplicate Username Registration ==="
REG_RESPONSE_2=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "finaluser", "email": "final_diff@example.com", "password": "password123"}')
echo $REG_RESPONSE_2

echo -e "\n=== 3. Login User ==="
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "final@example.com", "password": "password123"}')
echo $LOGIN_RESPONSE
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo -e "\n=== 4. Generate URL ==="
URL_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/urls \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://finaltest.com"}')
echo $URL_RESPONSE
SHORT_CODE=$(echo $URL_RESPONSE | grep -o '"short_code":"[^"]*' | cut -d'"' -f4)

echo -e "\n=== 5. Resolve URL ==="
curl -i -s http://127.0.0.1:8000/$SHORT_CODE | head -n 5

echo -e "\n\n=== 6. Invalid UUID Test ==="
curl -s -X PATCH http://127.0.0.1:8000/api/v1/urls/not-a-uuid \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
