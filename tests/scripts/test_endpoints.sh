#!/bin/bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!
sleep 2

echo -e "\n=== 1. Register User ==="
REG_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}')
echo $REG_RESPONSE

echo -e "\n=== 2. Login User ==="
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}')
echo $LOGIN_RESPONSE
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)

echo -e "\n=== 3. Refresh Token ==="
REFRESH_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}")
echo $REFRESH_RESPONSE

echo -e "\n=== 4. Generate URL ==="
URL_RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/urls \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://example.com"}')
echo $URL_RESPONSE
SHORT_CODE=$(echo $URL_RESPONSE | grep -o '"short_code":"[^"]*' | cut -d'"' -f4)

echo -e "\n=== 5. Resolve URL ==="
curl -i -s http://127.0.0.1:8000/$SHORT_CODE | head -n 5

kill $SERVER_PID
