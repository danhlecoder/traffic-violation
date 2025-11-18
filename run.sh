#!/bin/bash
# Deploy/Stop tất cả services trên 1 máy (192.168.1.43)

ACTION=${1:-up}

if [ "$ACTION" = "down" ]; then
    echo "🛑 Stopping ALL services..."
    echo ""

    docker compose -f docker-compose.frontend.yml down
    docker compose -f docker-compose.backend.yml down
    docker compose -f docker-compose.n8n.yml down
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
docker compose -f docker-compose.backend.yml down 2>/dev/null
docker compose -f docker-compose.n8n.yml down 2>/dev/null
docker compose -f docker-compose.frontend.yml down 2>/dev/null

echo ""
echo "2️⃣  Starting MongoDB Service (port 8002)..."
docker compose -f docker-compose.mongo.yml up -d --build

echo ""
echo "⏳ Waiting for MongoDB..."
sleep 5

echo ""
echo "3️⃣  Starting Backend Service (port 8000)..."
docker compose -f docker-compose.backend.yml up -d --build

echo ""
echo "⏳ Waiting for Backend..."
sleep 5

echo ""
echo "4️⃣  Starting N8N Automation Service (port 8001)..."
docker compose -f docker-compose.n8n.yml up -d

echo ""
echo "⏳ Waiting for N8N..."
sleep 5

echo ""
echo "5️⃣  Starting Frontend Service (port 3000)..."
docker compose -f docker-compose.frontend.yml up -d --build

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Services running on 192.168.1.43:"
echo "   - MongoDB:   http://192.168.1.43:27017"
echo "   - Mongo API: http://192.168.1.43:8002"
echo "   - Backend:   http://192.168.1.43:8000 (YOLO tích hợp sẵn)"
echo "   - N8N:       http://192.168.1.43:8001 👈 Automation & Workflows"
echo "   - Frontend:  http://192.168.1.43:3000"
echo ""
echo "🧪 Test services:"
echo "   curl http://192.168.1.43:8002/health"
echo "   curl http://192.168.1.43:8000/api/cameras"
echo "   curl http://192.168.1.43:8001/healthz"
echo ""
echo "🌐 Open browser:"
echo "   Frontend: http://192.168.1.43:3000"
echo "   N8N:      http://192.168.1.43:8001 (user: admin, pass: admin123)"
echo ""
echo "📊 View logs:"
echo "   docker compose -f docker-compose.mongo.yml logs -f"
echo "   docker compose -f docker-compose.backend.yml logs -f"
echo "   docker compose -f docker-compose.n8n.yml logs -f"
