# Traffic Violation — Dev Setup

## Yêu cầu
- Docker + Docker Compose

## Khởi động (Docker Compose)
1) Build & chạy:
   - Linux/macOS: `./run.sh`
   - Hoặc: `docker compose up --build`

2) Truy cập:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000/api/health


## Chạy thủ công (không dùng Docker)
```
pip install -r requirements.txt
```

Backend:
```
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```
cd frontend
npm i (lần đầu)
npm run dev -- --host 0.0.0.0 --port 5173
```
