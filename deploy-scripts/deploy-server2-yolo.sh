#!/bin/bash
# =====================================================
# Deploy YOLO Service - Server 2
# =====================================================
# Chạy script này trên Server 2 (YOLO Detection)
# IP Server 2: 192.168.1.20 (thay đổi nếu cần)

echo "🚀 Deploying YOLO Service trên Server 2..."
echo ""

# Stop service cũ
echo "1️⃣  Stopping old YOLO service..."
docker compose -f docker-compose.yolo.yml down 2>/dev/null

echo ""
echo "2️⃣  Starting YOLO Service..."
docker compose -f docker-compose.yolo.yml up -d --build

echo ""
echo "⏳ Waiting for YOLO to be ready..."
sleep 10

echo ""
echo "✅ YOLO Service deployed!"
echo ""
echo "📍 YOLO Service:"
echo "   - YOLO API:  http://192.168.1.20:8001"
echo ""
echo "🧪 Test YOLO API:"
echo "   curl http://192.168.1.20:8001/health"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.yolo.yml logs -f"
echo ""
