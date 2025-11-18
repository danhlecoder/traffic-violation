#!/bin/bash
# =====================================================
# Deploy MongoDB Service - Server 1
# =====================================================
# Chạy script này trên Server 1 (MongoDB + Mongo API)
# IP Server 1: 192.168.1.10 (thay đổi nếu cần)

echo "🚀 Deploying MongoDB Service trên Server 1..."
echo ""

# Stop service cũ
echo "1️⃣  Stopping old MongoDB service..."
docker compose -f docker-compose.mongo.yml down 2>/dev/null

echo ""
echo "2️⃣  Starting MongoDB Service..."
docker compose -f docker-compose.mongo.yml up -d --build

echo ""
echo "⏳ Waiting for MongoDB to be ready..."
sleep 8

echo ""
echo "✅ MongoDB Service deployed!"
echo ""
echo "📍 MongoDB Service:"
echo "   - MongoDB:    mongodb://admin:admin123@192.168.1.10:27017"
echo "   - Mongo API:  http://192.168.1.10:8002"
echo ""
echo "🧪 Test MongoDB API:"
echo "   curl http://192.168.1.10:8002/health"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.mongo.yml logs -f"
echo ""
