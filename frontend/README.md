# Traffic Violation UI — Frontend

Tài liệu ngắn gọn mô tả cấu trúc, vai trò thư mục và chức năng từng file chính trong `frontend/`.

## Mục lục nhanh
- Chạy dự án: `npm run dev`, build: `npm run build`
- Tech: React 18 + Vite + TypeScript, Zustand, Ant Design

## Cấu trúc thư mục

```
frontend/
├─ index.html                 # Điểm vào HTML cho Vite
├─ public/                    # Tài nguyên tĩnh (logo, placeholders)
├─ src/                       # Mã nguồn ứng dụng
│  ├─ App.tsx                 # Định tuyến trang, bố cục tổng
│  ├─ main.tsx                # Bootstrap React vào DOM
│  ├─ components/             # Thành phần tái sử dụng
│  │  ├─ Layout.tsx           # Khung layout (Header, Menu, Content)
│  │  ├─ Clock.tsx            # Đồng hồ realtime trên header
│  │  ├─ CameraTile.tsx       # Ô hiển thị camera (mock stream)
│  │  ├─ OperationLog.tsx     # Danh sách nhật ký thao tác
│  │  ├─ SectionHeader.tsx    # Header nhỏ cho từng khu vực
│  │  ├─ ThemeToggle.tsx      # Nút chuyển theme light/dark/system
│  │  ├─ charts/              # Biểu đồ đơn giản (SVG thuần)
│  │  │  ├─ SimpleBarChart.tsx  # Biểu đồ cột, hiển thị giá trị
│  │  │  ├─ SimplePieChart.tsx  # Biểu đồ tròn, có nhãn %
│  │  │  └─ utils.ts            # Hàm cung cấp bảng màu `palette`
│  │  └─ violations/          # Nhóm component cho tính năng Vi phạm
│  │     ├─ ViolationsFilter.tsx     # Bộ lọc (search/camera/loại/trạng thái/time)
│  │     ├─ ViolationList.tsx        # Danh sách vi phạm dạng thẻ đơn giản
│  │     ├─ ViolationCard.tsx        # Thẻ card (không bắt buộc dùng ở mọi nơi)
│  │     └─ ViolationDetailModal.tsx # Modal chi tiết (xem ảnh/video, xác nhận/bỏ qua)
│  ├─ constants/
│  │  └─ violations.ts        # Hằng số và mapper chung (trạng thái, màu tag, quy đổi loại)
│  ├─ pages/                  # Các trang chính
│  │  ├─ LiveMonitor.tsx      # Giám sát trực tiếp, lưới camera, pending list, modal chi tiết
│  │  ├─ Violations.tsx       # Danh sách vi phạm (bảng + bộ lọc + xuất CSV)
│  │  ├─ Reports.tsx          # Báo cáo (tổng quan, biểu đồ cột/tròn, đếm theo trạng thái)
│  │  ├─ Settings.tsx         # Cấu hình hệ thống + camera + tích hợp Zalo
│  │  └─ NotFound.tsx         # 404
│  ├─ providers/
│  │  └─ ThemeProvider.tsx    # Bọc Ant Design + đồng bộ theme, locale vi-VN
│  ├─ services/               # Tầng dịch vụ (API giả lập / tích hợp)
│  │  ├─ api.ts               # Re-export để tương thích ngược
│  │  ├─ violations.ts        # confirmViolation, skipViolation (mock)
│  │  └─ zalo.ts              # sendZalo (mock toast + delay)
│  ├─ store/                  # Zustand stores
│  │  ├─ useStore.ts          # Trạng thái vi phạm, logs, settings
│  │  └─ useTheme.ts          # Trạng thái theme và tính dark từ hệ thống
│  ├─ styles/
│  │  └─ global.css           # Biến theme + tinh chỉnh Ant Design + UI custom
│  └─ utils/
│     ├─ csv.ts               # Tạo và tải file CSV (downloadCsv, toCsv)
│     ├─ confirm.ts           # confirmAction (UI xác nhận đơn giản)
│     └─ media.ts             # isPlaceholder: nhận biết ảnh mock
├─ package.json               # Script, dependencies
├─ tsconfig.json              # Cấu hình TypeScript
└─ vite.config.ts             # Cấu hình Vite
```

## Luồng chính theo tính năng

- LiveMonitor
  - Sinh dữ liệu vi phạm demo (xóa khi backend); hiển thị lưới camera, bộ đếm theo loại.
  - Danh sách vi phạm “Chờ duyệt”; mở `ViolationDetailModal` để xem chi tiết và hành động.
  - Ghi nhật ký thao tác qua `useStore.addOperationLog`.

- Violations (Danh sách)
  - Bảng dữ liệu với bộ lọc `ViolationsFilter` (search, camera, loại, trạng thái, thời gian).
  - Xuất CSV qua `utils/csv.ts`.

- Reports (Báo cáo)
  - Tổng quan (tổng số, đã xác nhận), nhóm theo loại, hiển thị biểu đồ cột/tròn.
  - Biểu đồ tròn hiển thị % trực tiếp trên lát cắt; tag chú giải có kèm %.

- Settings (Cấu hình)
  - Thiết lập luật phát hiện, ngưỡng tốc độ, tích hợp Zalo, danh sách camera.

## Chỉnh sửa

- Nêu những thay đổi ở đây (sửa code)
- .......

