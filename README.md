# Traffic Violation — Dev Setup

Chạy nhanh bằng Docker (có cả backend FastAPI + frontend Vite React và stream RTSP → MJPEG).

## Yêu cầu
- Docker + Docker Compose

## Khởi động (Docker Compose)
1) Build & chạy:
   - Linux/macOS: `./run.sh`
   - Hoặc: `docker-compose up --build`

2) Truy cập:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000/api/health

3) Thêm camera RTSP:
   - Vào trang “Cấu hình” → “Quản lý Camera”, thêm dòng mới và điền `RTSP` (vd: `rtsp://user:pass@ip:554/stream`).
   - Mở “Giám sát trực tiếp” để xem luồng. Ảnh từ RTSP được backend chuyển thành MJPEG và hiển thị qua thẻ `<img>`.
   - Backend mặc định stream 30 FPS. Có thể chỉnh qua query `fps` (1–60) và `quality` (10–95), ví dụ:
     - `http://localhost:8000/api/stream?src=<RTSP_ENCODED>&fps=30&quality=80`

Ghi chú:
- Mặc định frontend gọi stream qua `http://<host>:8000/api/stream?src=...`. Bạn có thể tùy chỉnh base bằng biến môi trường `VITE_API_BASE` nếu cần.
- RTSP cần truy cập được từ máy chạy Docker. Nếu camera ở mạng khác, cần mở route/firewall phù hợp.

## Chạy thủ công (không dùng Docker)
Backend:
```
pip install -r requirements.txt
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```
cd frontend
npm i
npm run dev -- --host 0.0.0.0 --port 5173
```
