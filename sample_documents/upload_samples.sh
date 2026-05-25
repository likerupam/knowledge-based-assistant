#!/bin/bash

set -e

API_URL="http://localhost:8000"
UPLOAD_DIR="./sample_documents"

echo "======================================"
echo "TechCorp Knowledge Base Setup"
echo "======================================"
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🔍 Checking if API is running..."
if ! curl -s "$API_URL/health" > /dev/null; then
    echo -e "${RED}❌ API is not running at $API_URL${NC}"
    exit 1
fi
echo -e "${GREEN}✅ API is running${NC}"
echo ""

echo "📝 Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@techcorp.com",
    "password": "DemoPassword123!",
    "full_name": "Demo User"
  }')

echo -e "${GREEN}✅ User registration done${NC}"
echo ""

echo "🔐 Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@techcorp.com",
    "password": "DemoPassword123!"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to obtain access token${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Login successful${NC}"
echo ""

echo "📤 Uploading documents..."
echo ""

DOCUMENTS=(
    "employee_handbook.txt"
    "technical_docs.txt"
    "database_schema.sql"
    "application_logs.log"
    "security_policy.txt"
    "quarterly_report.txt"
    "generated/real_cloud_status_incidents.txt"
    "generated/real_cloud_status_insights.txt"
)

for doc in "${DOCUMENTS[@]}"; do
    FILE_PATH="$UPLOAD_DIR/$doc"
    
    if [ ! -f "$FILE_PATH" ]; then
        echo -e "${YELLOW}⚠️  File not found: $FILE_PATH${NC}"
        continue
    fi
    
    echo -n "Uploading $doc ... "
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/documents/upload" \
      -H "Authorization: Bearer $TOKEN" \
      -F "file=@$FILE_PATH")
    
    if echo "$RESPONSE" | grep -q "message"; then
        echo -e "${GREEN}✅ Success${NC}"
    else
        echo -e "${RED}❌ Failed${NC}"
    fi
done

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
