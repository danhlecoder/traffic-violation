#!/bin/bash

# Test API detect/stopline trực tiếp
# Tạo 1 ảnh base64 test đơn giản

echo "Testing POST /api/detect/stopline..."
echo ""

# Tạo request với ảnh sample (1x1 pixel)
RESPONSE=$(curl -s -X POST http://localhost:8000/api/detect/stopline \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
  }')

echo "Response:"
echo "$RESPONSE" | jq '.'
echo ""
echo "stopLine keys:"
echo "$RESPONSE" | jq 'keys'
echo ""
echo "Has lineB?"
echo "$RESPONSE" | jq 'has("lineB")'
