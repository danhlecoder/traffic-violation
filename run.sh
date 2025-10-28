#!/bin/bash
# Deploy/Stop tất cả services trên 1 máy (192.168.1.43)

ACTION=${1:-up}

if [ "$ACTION" = "down" ]; then
    echo "🛑 Stopping ALL services..."
    echo ""

    docker compose -f docker-compose.frontend.yml down
    docker compose -f docker-compose.backend.yml down
    docker compose -f docker-compose.yolo.yml down
    docker compose -f docker-compose.mongo.yml down
    docker compose down 2>/dev/null

    echo ""
    echo "✅ All services stopped!"
    exit 0
fi

if [ "$ACTION" != "up" ]; then
    echo "Usage: bash run.sh [up|down]"
    echo "  up   - Start all services (default)"
    echo "  down - Stop all services"
    exit 1
fi

echo "🚀 Deploying ALL services trên 192.168.1.43..."
echo ""

# Stop tất cả services cũ
echo "1️⃣  Stopping old services..."
docker compose down 2>/dev/null
docker compose -f docker-compose.mongo.yml down 2>/dev/null
docker compose -f docker-compose.yolo.yml down 2>/dev/null
docker compose -f docker-compose.backend.yml down 2>/dev/null
docker compose -f docker-compose.frontend.yml down 2>/dev/null

echo ""
echo "2️⃣  Starting MongoDB Service (port 8002)..."
docker compose -f docker-compose.mongo.yml up -d --build

echo ""
echo "⏳ Waiting for MongoDB..."
sleep 5

echo ""
echo "3️⃣  Starting YOLO Service (port 8001)..."
docker compose -f docker-compose.yolo.yml up -d --build

echo ""
echo "⏳ Waiting for YOLO..."
sleep 5

echo ""
echo "4️⃣  Starting Backend Service (port 8000)..."
docker compose -f docker-compose.backend.yml up -d --build

echo ""
echo "⏳ Waiting for Backend..."
sleep 5

echo ""
echo "5️⃣  Starting Frontend Service (port 3000)..."
docker compose -f docker-compose.frontend.yml up -d --build

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Services running on 192.168.1.43:"
echo "   - MongoDB:  http://192.168.1.43:27017"
echo "   - Mongo API: http://192.168.1.43:8002"
echo "   - YOLO API:  http://192.168.1.43:8001"
echo "   - Backend:   http://192.168.1.43:8000"
echo "   - Frontend:  http://192.168.1.43:3000"
echo ""
echo "🧪 Test services:"
echo "   curl http://192.168.1.43:8002/health"
echo "   curl http://192.168.1.43:8001/health"
echo "   curl http://192.168.1.43:8000/api/cameras"
echo ""
echo "🌐 Open browser: http://192.168.1.43:3000"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.mongo.yml logs -f"
echo "   docker compose -f docker-compose.yolo.yml logs -f"
echo "   docker compose -f docker-compose.backend.yml logs -f"
