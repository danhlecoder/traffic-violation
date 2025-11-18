# 🐳 DOCKER DEPLOYMENT - PROMPT

## 📋 Metadata
```yaml
tags: [deployment, docker, docker-compose, containers]
inputs:
  - docker-compose files
  - environment configs
  - service ports
tools:
  - Docker
  - Docker Compose
  - Shell scripts
output_format: Running containers
complexity: Medium
```

---

## 🎯 Chức năng

### Docker Architecture
**Mục đích**: Deploy ứng dụng bằng Docker containers

**Files liên quan**:
- `docker-compose.mongo.yml` - MongoDB service
- `docker-compose.yolo.yml` - YOLO detection service
- `docker-compose.backend.yml` - FastAPI backend
- `docker-compose.frontend.yml` - React frontend
- `deploy-scripts/` - Automation scripts

**Deployment Modes**:
1. **Single Server**: Tất cả services trên 1 máy
2. **Multi Server**: Mỗi service trên 1 máy riêng

---

## ✅ Checklist Pre-Deployment

### 1. System Requirements
- [ ] Docker version >= 20.10
- [ ] Docker Compose version >= 2.0
- [ ] RAM >= 8GB (16GB recommended)
- [ ] Disk space >= 50GB
- [ ] GPU support (nếu dùng YOLO)

### 2. Network Setup
- [ ] Ports available: 27017 (MongoDB), 8001 (YOLO), 8000 (Backend), 3000 (Frontend)
- [ ] Firewall rules configured
- [ ] Internal network cho services
- [ ] External access nếu cần

### 3. Environment Files
- [ ] Copy `.env.example` → `.env`
- [ ] Configure MongoDB connection string
- [ ] Configure YOLO service URL
- [ ] Set API keys nếu có
- [ ] Set production URLs

### 4. Volume Mounts
- [ ] Create logs directory
- [ ] Create models directory (YOLO weights)
- [ ] Create data directory (MongoDB data)
- [ ] Create evidence directory (violation images)
- [ ] Set permissions (chmod, chown)

---

## ✅ Checklist Deployment Steps

### Single Server Deployment

#### 1. Build Images
- [ ] Build MongoDB service: `docker-compose -f docker-compose.mongo.yml build`
- [ ] Build YOLO service: `docker-compose -f docker-compose.yolo.yml build`
- [ ] Build Backend: `docker-compose -f docker-compose.backend.yml build`
- [ ] Build Frontend: `docker-compose -f docker-compose.frontend.yml build`

#### 2. Start Services (Thứ tự quan trọng!)
- [ ] Start MongoDB first: `docker-compose -f docker-compose.mongo.yml up -d`
- [ ] Wait MongoDB ready (check logs)
- [ ] Start YOLO service: `docker-compose -f docker-compose.yolo.yml up -d`
- [ ] Wait YOLO ready (load models)
- [ ] Start Backend: `docker-compose -f docker-compose.backend.yml up -d`
- [ ] Wait Backend ready (health check)
- [ ] Start Frontend: `docker-compose -f docker-compose.frontend.yml up -d`

#### 3. Verify Services
- [ ] Check all containers running: `docker ps`
- [ ] Check MongoDB connection: `docker exec mongo mongosh`
- [ ] Check YOLO API: `curl http://localhost:8001/health`
- [ ] Check Backend API: `curl http://localhost:8000/health`
- [ ] Check Frontend: Open browser `http://localhost:3000`

### Multi Server Deployment

#### Server 1 - MongoDB
- [ ] Copy `mongo-service/` files
- [ ] Configure `.env` với external access
- [ ] Start: `docker-compose -f docker-compose.mongo.yml up -d`
- [ ] Allow connections from other servers

#### Server 2 - YOLO  
- [ ] Copy `yolo-service/` files
- [ ] Download YOLO weights
- [ ] Configure MongoDB URL (Server 1)
- [ ] Start: `docker-compose -f docker-compose.yolo.yml up -d`

#### Server 3 - Backend
- [ ] Copy `backend/` files
- [ ] Configure MongoDB URL (Server 1)
- [ ] Configure YOLO URL (Server 2)
- [ ] Start: `docker-compose -f docker-compose.backend.yml up -d`

#### Server 4 - Frontend
- [ ] Copy `frontend/` files
- [ ] Configure Backend API URL (Server 3)
- [ ] Build production: `npm run build`
- [ ] Start: `docker-compose -f docker-compose.frontend.yml up -d`

---

## ⚠️ Pitfalls - Lỗi thường gặp

### 1. Service Start Order
❌ **Sai**: Start tất cả cùng lúc
- Kết quả: Backend không connect được MongoDB

✅ **Đúng**: Start theo thứ tự: MongoDB → YOLO → Backend → Frontend

### 2. Port Conflicts
❌ **Sai**: Port 27017 đã được dùng
- Kết quả: MongoDB container không start

✅ **Đúng**: Check ports trước: `netstat -tulpn | grep 27017`

### 3. Volume Permissions
❌ **Sai**: MongoDB data volume không có quyền write
- Kết quả: Container crash do không ghi được data

✅ **Đúng**: `chmod 777 ./data` hoặc set owner đúng

### 4. Environment Variables
❌ **Sai**: Dùng localhost trong container
- Kết quả: Containers không kết nối được nhau

✅ **Đúng**: Dùng service names hoặc host.docker.internal

### 5. Memory Limits
❌ **Sai**: Không set memory limits
- Kết quả: YOLO service eat hết RAM

✅ **Đúng**: Set trong docker-compose: `mem_limit: 4g`

### 6. GPU Support
❌ **Sai**: Không config GPU trong docker-compose
- Kết quả: YOLO chạy trên CPU, rất chậm

✅ **Đúng**: Thêm `runtime: nvidia` và `deploy.resources.reservations.devices`

### 7. Network Issues
❌ **Sai**: Services không cùng network
- Kết quả: Không resolve được service names

✅ **Đúng**: Define shared network trong docker-compose

### 8. Health Checks
❌ **Sai**: Không có health checks
- Kết quả: Start service tiếp theo khi previous chưa ready

✅ **Đúng**: Thêm healthcheck trong docker-compose

---

## 📝 Configuration Examples

### Example 1: docker-compose.mongo.yml (Basic)
**Checklist**:
- [ ] Service name: `mongodb`
- [ ] Image: `mongo:7.0`
- [ ] Port: `27017:27017`
- [ ] Volume: `./data:/data/db`
- [ ] Environment: `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`
- [ ] Network: `traffic-network`
- [ ] Restart: `always`

### Example 2: docker-compose.yolo.yml (GPU)
**Checklist**:
- [ ] Service name: `yolo-service`
- [ ] Build: `./yolo-service`
- [ ] Port: `8001:8001`
- [ ] Volume: `./models:/app/models`
- [ ] Runtime: `nvidia` (for GPU)
- [ ] Environment: `MONGODB_URL`, `MODEL_PATH`
- [ ] Depends_on: `mongodb`
- [ ] Memory limit: `4g`

### Example 3: Backend with Health Check
**Checklist**:
- [ ] Healthcheck command: `curl -f http://localhost:8000/health`
- [ ] Interval: `30s`
- [ ] Timeout: `10s`
- [ ] Retries: `3`
- [ ] Start period: `40s`

---

## 🔧 Deployment Scripts Checklist

### deploy-server1-mongo.sh
- [ ] Check Docker installed
- [ ] Check ports available
- [ ] Create data directories
- [ ] Set permissions
- [ ] Pull/build image
- [ ] Start container
- [ ] Verify connection
- [ ] Show logs

### deploy-server2-yolo.sh
- [ ] Check GPU available
- [ ] Download YOLO weights
- [ ] Configure MongoDB connection
- [ ] Build image
- [ ] Start container
- [ ] Test inference
- [ ] Monitor GPU usage

### deploy-server3-backend.sh
- [ ] Configure service URLs
- [ ] Install dependencies
- [ ] Build image
- [ ] Start container
- [ ] Run health check
- [ ] Test API endpoints

---

## 🧪 Testing Checklist

### Container Health
- [ ] All containers status = "running"
- [ ] No containers restarting repeatedly
- [ ] Logs không có errors critical

### Connectivity
- [ ] Backend → MongoDB: OK
- [ ] Backend → YOLO: OK
- [ ] Frontend → Backend: OK
- [ ] External access: OK

### Performance
- [ ] CPU usage < 80%
- [ ] Memory usage < 80%
- [ ] Network latency < 100ms
- [ ] Response time < 1s

### Data Persistence
- [ ] Stop containers → data vẫn còn
- [ ] Restart containers → data intact
- [ ] Volume mounts correct

---

## 🐛 Troubleshooting Checklist

### Container không start
- [ ] Check logs: `docker logs <container_name>`
- [ ] Check ports: `netstat -tulpn`
- [ ] Check disk space: `df -h`
- [ ] Check permissions: `ls -la`

### Service không kết nối được
- [ ] Ping service: `docker exec backend ping mongodb`
- [ ] Check network: `docker network ls`
- [ ] Check DNS: `docker exec backend nslookup mongodb`
- [ ] Check firewall rules

### Performance kém
- [ ] Check resource usage: `docker stats`
- [ ] Check logs for errors
- [ ] Monitor GPU usage: `nvidia-smi`
- [ ] Check network traffic

### Data loss
- [ ] Check volume mounts: `docker inspect <container>`
- [ ] Verify backup strategy
- [ ] Check filesystem errors

---

## 📊 Monitoring Checklist

### Metrics to Track
- [ ] Container uptime
- [ ] CPU/Memory usage per service
- [ ] Network I/O
- [ ] Disk I/O
- [ ] API response times
- [ ] Error rates

### Logging
- [ ] Centralized logging (ELK stack)
- [ ] Log rotation configured
- [ ] Log levels appropriate
- [ ] Sensitive data masked

---

## 🔗 Related Prompts

- `deployment/single-server.prompt.md` - Single server setup
- `deployment/multi-server.prompt.md` - Multi server architecture
- `deployment/troubleshoot.prompt.md` - Debug deployment issues
- `workflows/testing.prompt.md` - Testing deployed services
