#!/bin/bash
# =====================================================
# Deploy Backend Service - Server 2
# =====================================================
# Chạy script này trên Server 2 (Backend API - YOLO tích hợp sẵn)
# IP Server 2: 192.168.1.20 (thay đổi nếu cần)

echo "🚀 Deploying Backend Service trên Server 2..."
echo ""

# Kiểm tra file .env
if [ ! -f "backend/.env" ]; then
    echo "❌ Error: backend/.env không tồn tại!"
    echo ""
    echo "Vui lòng copy file mẫu và chỉnh sửa IP:"
    echo "1. cp backend/.env.multi-server backend/.env"
    echo "2. nano backend/.env"
    echo "3. Sửa dòng:"
    echo "   YOLO_API_URL=http://[IP_SERVER_2]:8001"
    echo "   MONGO_API_URL=http://[IP_SERVER_1]:8002"
    echo ""
    echo "Chi tiết xem: HUONG_DAN_DOI_IP.md"
    exit 1
fi

echo "✓ Found backend/.env"
echo ""
echo "⚠️  QUAN TRỌNG: Đảm bảo đã sửa IP trong backend/.env:"
echo "   MONGO_API_URL=http://[IP_SERVER_1]:8002"
echo ""
read -p "Đã sửa IP đúng chưa? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Vui lòng sửa backend/.env trước khi deploy!"
    exit 1
fi

# Stop service cũ
echo "1️⃣  Stopping old Backend service..."
docker compose -f docker-compose.backend.yml down 2>/dev/null

echo ""
echo "2️⃣  Starting Backend Service..."
docker compose -f docker-compose.backend.yml up -d --build

echo ""
echo "⏳ Waiting for Backend to be ready..."
sleep 8

echo ""
echo "✅ Backend Service deployed!"
echo ""
echo "📍 Backend Service:"
echo "   - Backend API:  http://192.168.1.20:8000 (YOLO tích hợp sẵn)"
echo ""
echo "🧪 Test Backend API:"
echo "   curl http://192.168.1.20:8000/api/cameras"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.backend.yml logs -f"
echo ""
