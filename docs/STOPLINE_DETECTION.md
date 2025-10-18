# Tài Liệu: Phát Hiện Vạch Dừng (Stopline Detection)

## Tổng Quan

Hệ thống phát hiện vạch dừng với logic thông minh dựa trên việc phát hiện đèn giao thông.

## Logic Hoạt Động

### 1. Quy trình chính (`detect_stop_line_with_fallback`)

Khi nhận được frame ảnh đầu tiên:

```
Frame đầu tiên
     ↓
Kiểm tra traffic light (light_red, light_green, light_yellow)
     ↓
     ├─→ CÓ traffic light
     │        ↓
     │   Sử dụng detect line TỰ ĐỘNG (Canny + HoughLinesP)
     │        ↓
     │   ├─→ Phát hiện thành công → Trả về tọa độ line
     │   └─→ Thất bại → Tạo line mặc định 2/3
     │
     └─→ KHÔNG có traffic light
              ↓
         Tạo line mặc định ở vị trí 2/3 chiều cao
```

### 2. Các trường hợp xử lý

#### Trường hợp 1: Có đèn giao thông
- **Điều kiện**: Phát hiện class `light_red`, `light_green` hoặc `light_yellow`
- **Xử lý**: Sử dụng thuật toán Canny + HoughLinesP để tự động phát hiện vạch dừng
- **Kết quả**: Tọa độ line thực tế hoặc line mặc định nếu thất bại

#### Trường hợp 2: Không có đèn giao thông
- **Điều kiện**: Không phát hiện class đèn giao thông nào
- **Xử lý**: Tạo line ngang ở vị trí 2/3 chiều cao ảnh
- **Kết quả**: Line mặc định tại `y = 0.667` (normalized)

### 3. Tọa độ chuẩn hóa

Tất cả tọa độ được chuẩn hóa về khoảng `[0, 1]`:
- `x = 0.0`: Biên trái ảnh
- `x = 1.0`: Biên phải ảnh
- `y = 0.0`: Biên trên ảnh
- `y = 1.0`: Biên dưới ảnh

Line mặc định: `((0.0, 0.667), (1.0, 0.667))`
- Line ngang từ trái sang phải tại vị trí 2/3 chiều cao

## API Endpoint

### POST `/api/detect/stopline`

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
  "stopLine": [
    {"x": 0.0, "y": 0.667},
    {"x": 1.0, "y": 0.667}
  ]
}
```

## Các Function Chính

### 1. `detect_stop_line_with_fallback(frame_bgr)`
- **Mô tả**: Function chính xử lý logic phát hiện stopline với fallback
- **Input**: Frame ảnh BGR (numpy array)
- **Output**: Tuple 2 điểm chuẩn hóa hoặc line mặc định

### 2. `_has_traffic_lights(frame_bgr)`
- **Mô tả**: Kiểm tra xem frame có chứa đèn giao thông không
- **Input**: Frame ảnh BGR
- **Output**: `True` nếu có traffic light, `False` nếu không

### 3. `_create_default_stopline()`
- **Mô tả**: Tạo line mặc định ở vị trí 2/3
- **Output**: Tuple 2 điểm `((0.0, 0.667), (1.0, 0.667))`

### 4. `detect_stop_line_normalized(frame_bgr)`
- **Mô tả**: Phát hiện line tự động bằng Canny + HoughLinesP
- **Input**: Frame ảnh BGR
- **Output**: Tuple 2 điểm chuẩn hóa hoặc `None`

## Cấu Hình

Các tham số cấu hình trong `settings`:

```python
# Canny edge detection
VISION_CANNY_LOW = 50
VISION_CANNY_HIGH = 150

# HoughLinesP
VISION_HOUGH_RHO = 1
VISION_HOUGH_THETA = np.pi / 180
VISION_HOUGH_THRESHOLD = 50
VISION_MIN_LINE_LEN_FACTOR = 0.3
VISION_MAX_GAP_FACTOR = 0.05

# Line filtering
VISION_ANGLE_MAX_DEG = 15
VISION_CENTER_BIAS_RATIO = 0.4
VISION_BOTTOM_MIN_Y_RATIO = 0.5
```

## Logging

Hệ thống ghi log chi tiết:
- ✓ Phát hiện đèn giao thông thành công
- ✗ Không phát hiện đèn giao thông
- ✓ Detect line thành công
- ⚠ Sử dụng line mặc định

## Use Case

### Ví dụ 1: Camera có đèn giao thông
```
Input: Frame từ camera giao lộ (có traffic light)
Process: 
  1. Phát hiện light_red → has_traffic_light = True
  2. Chạy detect line tự động
  3. Tìm thấy vạch dừng tại y = 0.72
Output: ((0.0, 0.72), (1.0, 0.72))
```

### Ví dụ 2: Camera không có đèn giao thông
```
Input: Frame từ camera cao tốc (không có traffic light)
Process:
  1. Không phát hiện traffic light → has_traffic_light = False
  2. Tạo line mặc định
Output: ((0.0, 0.667), (1.0, 0.667))
```

### Ví dụ 3: Có đèn nhưng không tìm thấy vạch
```
Input: Frame có traffic light nhưng vạch dừng bị mờ
Process:
  1. Phát hiện light_green → has_traffic_light = True
  2. Chạy detect line tự động → Thất bại (None)
  3. Fallback về line mặc định
Output: ((0.0, 0.667), (1.0, 0.667))
```

## Lưu Ý Kỹ Thuật

1. **Performance**: 
   - Kiểm tra traffic light chỉ chạy 1 lần trên frame đầu tiên
   - YOLO model được load singleton để tránh load lại nhiều lần

2. **Error Handling**:
   - Tất cả exceptions đều được catch và fallback về line mặc định
   - Đảm bảo luôn trả về kết quả hợp lệ

3. **Tọa độ**:
   - Luôn sử dụng tọa độ normalized [0, 1]
   - Tránh hardcode pixel values

4. **Frame Preprocessing**:
   - Frame được crop về tỷ lệ 16:9 trước khi xử lý
   - Downscale về 960x540 để tăng tốc detection

## Files Liên Quan

- `/backend/services/detect_line.py` - Logic phát hiện line
- `/backend/services/detector.py` - YOLO detector
- `/backend/api/streams.py` - API endpoint
- `/backend/core/config.py` - Cấu hình

## Changelog

### v1.1.0 - Thêm Logic Traffic Light Fallback
- Thêm `detect_stop_line_with_fallback()` function
- Thêm `_has_traffic_lights()` helper
- Thêm `_create_default_stopline()` helper
- Cập nhật API endpoint sử dụng logic mới
- Thêm logging chi tiết cho debugging
