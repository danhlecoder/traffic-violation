#!/bin/bash
# =====================================================
# Deploy Frontend Service - Server 4
# =====================================================
# Chạy script này trên Server 4 (Frontend Web)
# IP Server 4: 192.168.1.40 (thay đổi nếu cần)

echo "🚀 Deploying Frontend Service trên Server 4..."
echo ""

# Kiểm tra file .env.production.local
ENV_FILE="frontend/.env.production.local"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Warning: $ENV_FILE không tồn tại!"
    echo ""
    echo "Vui lòng tạo file config:"
    echo "1. cp frontend/.env.example frontend/.env.production.local"
    echo "2. nano frontend/.env.production.local"
    echo "3. Sửa dòng:"
    echo "   VITE_API_BASE_URL=http://[IP_SERVER_3]:8000"
    echo ""
    echo "Chi tiết xem: HUONG_DAN_DOI_IP.md"
    echo ""
    read -p "Có muốn copy file mẫu ngay bây giờ? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "frontend/.env.example" ]; then
            cp frontend/.env.example "$ENV_FILE"
            echo "✓ Đã copy frontend/.env.example → $ENV_FILE"
            echo ""
            echo "⚠️  VUI LÒNG SỬA IP trong file $ENV_FILE trước khi tiếp tục!"
            read -p "Nhấn Enter khi đã sửa xong..." 
        else
            echo "❌ Không tìm thấy frontend/.env.example"
            exit 1
        fi
    else
        echo "Vui lòng tạo file thủ công và chạy lại script!"
        exit 1
    fi
fi

echo "✓ Found $ENV_FILE"
echo ""
echo "⚠️  QUAN TRỌNG: Đảm bảo đã sửa IP trong $ENV_FILE:"
echo "   VITE_API_BASE_URL=http://[IP_SERVER_3]:8000"
echo ""
read -p "Đã sửa IP đúng chưa? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Vui lòng sửa $ENV_FILE trước khi deploy!"
    exit 1
fi

# Stop service cũ
echo "1️⃣  Stopping old Frontend service..."
docker compose -f docker-compose.frontend.yml down 2>/dev/null

echo ""
echo "2️⃣  Starting Frontend Service..."
docker compose -f docker-compose.frontend.yml up -d --build

echo ""
echo "⏳ Waiting for Frontend to be ready..."
sleep 5

echo ""
echo "✅ Frontend Service deployed!"
echo ""
echo "📍 Frontend Service:"
echo "   - Frontend Web:  http://192.168.1.40:3000"
echo ""
echo "🌐 Mở trình duyệt:"
echo "   http://192.168.1.40:3000"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.frontend.yml logs -f"
echo ""
