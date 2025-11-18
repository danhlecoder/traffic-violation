# 📚 COMMANDS - PROMPTS TRA CỨU NHANH

## 🎯 Mục đích
Thư mục này chứa các prompts/rules nhỏ, tập trung vào từng chức năng cụ thể để AI Agent hiểu dự án mà không cần đọc toàn bộ repo.

## 🏗️ Cấu trúc thư mục

```
commands/
├── README.md                    # File này - hướng dẫn tổng quan
├── INDEX.md                     # Index tra cứu nhanh theo tags
│
├── api/                         # Prompts về API endpoints
│   ├── violations.prompt.md     # Xử lý violations API
│   ├── cameras.prompt.md        # Quản lý cameras API  
│   ├── streams.prompt.md        # Video streaming API
│   └── detection.prompt.md      # Detection API
│
├── database/                    # Prompts về MongoDB
│   ├── schema.prompt.md         # Cấu trúc database schema
│   ├── queries.prompt.md        # Các queries thường dùng
│   └── migrations.prompt.md     # Migration và update schema
│
├── detection/                   # Prompts về phát hiện vi phạm
│   ├── yolo.prompt.md          # YOLO vehicle detection
│   ├── license-plate.prompt.md  # Nhận diện biển số
│   ├── tracking.prompt.md       # Tracking xe qua frames
│   └── violations.prompt.md     # Logic phát hiện vi phạm
│
├── deployment/                  # Prompts về triển khai
│   ├── docker.prompt.md        # Docker setup và deploy
│   ├── single-server.prompt.md  # Deploy 1 server
│   ├── multi-server.prompt.md   # Deploy nhiều servers
│   └── troubleshoot.prompt.md   # Xử lý lỗi deploy
│
├── frontend/                    # Prompts về React UI
│   ├── components.prompt.md     # Các components chính
│   ├── services.prompt.md       # API services layer
│   └── state-management.prompt.md # Quản lý state
│
└── workflows/                   # Prompts về quy trình làm việc
    ├── new-feature.prompt.md    # Thêm tính năng mới
    ├── bug-fix.prompt.md        # Fix bug workflow
    ├── code-review.prompt.md    # Review code checklist
    └── testing.prompt.md        # Testing guidelines

```

## 📋 Cấu trúc mỗi Prompt File

Mỗi file `.prompt.md` có cấu trúc chuẩn:

### 1. Metadata Header
- **Tags**: Từ khóa để tìm kiếm
- **Inputs**: Thông tin cần có
- **Tools**: Công cụ/thư viện liên quan
- **Output**: Kết quả mong muốn

### 2. Context
- Giải thích chức năng
- Vị trí trong hệ thống
- Mối quan hệ với modules khác

### 3. Checklist
- Các bước cần làm
- Điều kiện cần kiểm tra

### 4. Pitfalls
- Lỗi thường gặp
- Điều cần tránh

### 5. Examples
- Ví dụ cụ thể
- Use cases thực tế

## 🔍 Cách sử dụng

### Cho AI Agent:
1. Đọc `INDEX.md` để tìm prompt phù hợp theo tags
2. Đọc 1-2 prompt files liên quan thay vì đọc toàn bộ repo
3. Áp dụng checklist và tránh pitfalls

### Cho Developer:
1. Tìm chức năng cần làm
2. Đọc prompt tương ứng
3. Follow checklist và examples

## 🏷️ Tags phổ biến

- `#api` - Liên quan API endpoints
- `#database` - MongoDB operations
- `#detection` - Computer vision, YOLO
- `#tracking` - Object tracking
- `#deployment` - Docker, deploy
- `#frontend` - React, UI
- `#bug-fix` - Sửa lỗi
- `#performance` - Tối ưu hiệu năng
- `#testing` - Unit test, integration test

## ⚡ Quick Start

Ví dụ Agent muốn fix bug về license plate detection:
1. Mở `INDEX.md`
2. Tìm tag `#license-plate` hoặc `#bug-fix`
3. Đọc `detection/license-plate.prompt.md`
4. Follow checklist và check pitfalls
5. Implement fix

## 🔄 Cập nhật

Khi thêm tính năng mới hoặc thay đổi architecture:
1. Tạo/cập nhật prompt file tương ứng
2. Cập nhật `INDEX.md`
3. Thêm examples thực tế
