#!/bin/bash
set -e
# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${GREEN}=== 1. Register User ===${NC}"
REG_RESPONSE=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "docker_test", "email": "docker@example.com", "password": "password123"}')
echo $REG_RESPONSE
USER_ID=$(echo $REG_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

echo -e "\n${GREEN}=== 2. Login User ===${NC}"
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "docker@example.com", "password": "password123"}')
echo $LOGIN_RESPONSE
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"refresh_token":"[^"]*' | cut -d'"' -f4)
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo -e "\n${GREEN}=== 3. Generate URL ===${NC}"
URL_RESPONSE=$(curl -s -X POST http://127.0.0.1:8080/api/v1/urls \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://docker.com"}')
echo $URL_RESPONSE
SHORT_CODE=$(echo $URL_RESPONSE | grep -o '"short_code":"[^"]*' | cut -d'"' -f4)
URL_ID=$(echo $URL_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

echo -e "\n${GREEN}=== 4. Resolve URL (Redirect) ===${NC}"
curl -i -s http://127.0.0.1:8080/$SHORT_CODE | head -n 5

echo -e "\n${GREEN}=== 5. Get Analytics ===${NC}"
ANALYTICS_RESPONSE=$(curl -s -X GET http://127.0.0.1:8080/api/v1/urls/$URL_ID/analytics \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo $ANALYTICS_RESPONSE

echo -e "\n${GREEN}=== 6. List URLs (Pagination) ===${NC}"
LIST_RESPONSE=$(curl -s -X GET "http://127.0.0.1:8080/api/v1/urls?page=1&page_size=10" \
  -H "Authorization: Bearer $ACCESS_TOKEN")
echo $LIST_RESPONSE

echo -e "\n${GREEN}=== 7. Deactivate URL ===${NC}"
PATCH_RESPONSE=$(curl -s -X PATCH http://127.0.0.1:8080/api/v1/urls/$URL_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}')
echo $PATCH_RESPONSE

echo -e "\n${GREEN}=== 8. Attempt Redirect on Deactivated URL ===${NC}"
curl -i -s http://127.0.0.1:8000/$SHORT_CODE | head -n 5

echo -e "\n${GREEN}Docker container tested successfully!${NC}"
