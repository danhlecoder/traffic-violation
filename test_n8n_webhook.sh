#!/bin/bash
# Script test N8N webhook

echo "🧪 Testing N8N Production Webhook..."
echo "URL: http://192.168.1.36:8001/webhook/violation-confirmed"
echo ""

curl -X POST http://192.168.1.36:8001/webhook/violation-confirmed \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": "test_manual_'$(date +%s)'",
    "timestamp": "'$(date -Iseconds)'",
    "location": "Test Location - Manual",
    "vehicle_type": "motorcycle",
    "license_plate": "TEST-001",
    "violation_tags": ["red_light"],
    "speed": 45,
    "images": {
      "full_frame": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
      "vehicle_crop": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
      "plate_crop": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }
  }' | jq .

echo ""
echo "✅ Nếu thấy response OK, check Discord channel!"



