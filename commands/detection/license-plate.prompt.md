# 🚗 LICENSE PLATE DETECTION - PROMPT

## 📋 Metadata
```yaml
tags: [detection, ocr, license-plate, computer-vision]
inputs:
  - vehicle_crop (numpy array)
  - vehicle_bbox (x1,y1,x2,y2)
  - confidence_threshold (float, default=0.5)
tools:
  - PaddleOCR hoặc EasyOCR
  - OpenCV
  - numpy
output_format: 
  - plate_text (string)
  - confidence (float)
  - bbox (coordinates)
complexity: High
```

---

## 🎯 Chức năng

### Module: License Plate Detector
**Mục đích**: Phát hiện và đọc biển số xe từ vehicle crop

**Vị trí file**: `backend/core/license_plate/detector.py`

**Pipeline**:
1. Nhận vehicle crop từ YOLO detection
2. Tìm vùng biển số trong crop
3. OCR đọc ký tự trên biển số
4. Validate format biển số VN
5. Return text và confidence

---

## ✅ Checklist Detection Flow

### 1. Preprocessing
- [ ] Resize vehicle crop về kích thước phù hợp
- [ ] Convert sang grayscale
- [ ] Apply adaptive threshold
- [ ] Denoise (Gaussian blur)
- [ ] Enhance contrast (CLAHE)

### 2. Plate Localization
- [ ] Detect plate region trong vehicle crop
- [ ] Dùng contour detection hoặc ML model
- [ ] Validate tỷ lệ width/height (3:1 đến 5:1)
- [ ] Filter theo area size
- [ ] Chọn best candidate

### 3. OCR
- [ ] Straighten plate (perspective transform)
- [ ] Segment characters
- [ ] Run OCR engine
- [ ] Post-process text (remove spaces, special chars)
- [ ] Validate character count (7-10 ký tự)

### 4. Validation Format VN
- [ ] Check format: XX-YYYYY hoặc XX-YYYYY
- [ ] Validate province code (29, 30, 51, 59, etc)
- [ ] Check character pattern (số-chữ-số)
- [ ] Confidence threshold >= 0.5

### 5. Error Handling
- [ ] Không detect được plate → return None
- [ ] OCR confidence thấp → flag for manual review
- [ ] Multiple plates → chọn confidence cao nhất
- [ ] Invalid format → attempt fuzzy matching

---

## ⚠️ Pitfalls - Lỗi thường gặp

### 1. Preprocessing không đủ
❌ **Sai**: OCR trực tiếp raw image
- Kết quả: Độ chính xác thấp, nhiều noise

✅ **Đúng**: Preprocessing đầy đủ (grayscale, threshold, denoise)

### 2. Không validate format
❌ **Sai**: Accept bất kỳ text nào OCR trả về
- Kết quả: "ABC123XYZ" không phải biển số VN

✅ **Đúng**: Validate theo format biển số VN

### 3. Confidence threshold quá thấp
❌ **Sai**: threshold=0.1 → Accept mọi kết quả
- Kết quả: Nhiều false positives

✅ **Đúng**: threshold=0.5 hoặc 0.6

### 4. Không handle góc chụp nghiêng
❌ **Sai**: OCR plate bị nghiêng
- Kết quả: Đọc sai ký tự

✅ **Đúng**: Perspective transform để straighten

### 5. Performance issues
❌ **Sai**: OCR full resolution image
- Kết quả: Chậm, tốn RAM

✅ **Đúng**: Resize về size phù hợp (width=300-400px)

### 6. Không cache OCR model
❌ **Sai**: Load model mỗi lần detect
- Kết quả: Startup time lâu

✅ **Đúng**: Load model 1 lần khi init

---

## 📝 Implementation Examples

### Example 1: Success case
**Input**: 
- Vehicle crop: 640x480 image
- Vehicle bbox: (100, 200, 400, 500)

**Processing**:
1. Extract plate region → 200x60 crop
2. Preprocess → Enhanced grayscale
3. OCR → "29A12345"
4. Validate → Valid VN format
5. Confidence → 0.87

**Output**:
```
{
  "plate_text": "29A-12345",
  "confidence": 0.87,
  "bbox": [150, 250, 350, 310],
  "province": "Hà Nội"
}
```

### Example 2: Low confidence
**Input**: Blurry image, poor lighting

**Output**:
```
{
  "plate_text": "29A-1234?",
  "confidence": 0.42,
  "bbox": [150, 250, 350, 310],
  "requires_review": true
}
```

### Example 3: Detection failed
**Input**: Xe không có biển số visible

**Output**:
```
{
  "plate_text": null,
  "confidence": 0.0,
  "error": "No plate detected"
}
```

---

## 🔧 Configuration Checklist

### Model Selection
- [ ] Chọn OCR engine (PaddleOCR recommended)
- [ ] Download pretrained weights
- [ ] Configure model path trong config

### Thresholds
- [ ] plate_confidence_threshold = 0.5
- [ ] ocr_confidence_threshold = 0.6
- [ ] min_plate_area = 1000 pixels
- [ ] max_plate_area = 50000 pixels

### Preprocessing
- [ ] gaussian_blur_kernel = (5, 5)
- [ ] adaptive_threshold_block_size = 11
- [ ] clahe_clip_limit = 2.0

### Performance
- [ ] max_image_width = 400
- [ ] use_gpu = True nếu available
- [ ] batch_processing nếu nhiều plates

---

## 🧪 Testing Checklist

### Test Cases
- [ ] Biển số rõ nét, góc thẳng → confidence > 0.8
- [ ] Biển số nghiêng → vẫn detect được
- [ ] Biển số mờ, lighting kém → confidence < 0.5
- [ ] Không có biển số → return None
- [ ] Nhiều biển số (xe tải + xe con) → detect nhiều
- [ ] Biển số VN mới (chữ trước số) → detect đúng
- [ ] Biển số nước ngoài → reject

### Performance Test
- [ ] Processing time < 100ms per plate
- [ ] Memory usage < 500MB
- [ ] Accuracy > 85% trên test set

### Edge Cases
- [ ] Biển số bị che khuất một phần
- [ ] Biển số bẩn, mờ
- [ ] Biển số phản chiếu ánh sáng
- [ ] Night time, low light
- [ ] Rain, fog conditions

---

## 🐛 Debugging Checklist

Khi OCR không chính xác:

### 1. Check preprocessing
- [ ] Visualize preprocessed image
- [ ] Check contrast, brightness
- [ ] Verify plate crop có đúng region không

### 2. Check OCR output
- [ ] Print raw OCR text
- [ ] Check confidence scores từng ký tự
- [ ] Visualize bounding boxes

### 3. Check validation
- [ ] Log rejected plates
- [ ] Verify regex pattern
- [ ] Check province code list

### 4. Check model
- [ ] Verify model weights loaded
- [ ] Check model version
- [ ] Try different OCR engine

---

## 📊 Metrics to Monitor

### Accuracy Metrics
- **Precision**: Plates detected đúng / Total detected
- **Recall**: Plates detected đúng / Total actual plates
- **Character Accuracy**: Ký tự đúng / Total characters
- **Full Match Rate**: Biển số đúng 100% / Total

### Performance Metrics
- **Processing Time**: Average time per frame
- **Throughput**: Plates per second
- **Memory Usage**: RAM consumption

### Quality Metrics
- **Average Confidence**: Mean confidence scores
- **Low Confidence Rate**: % plates < threshold
- **Manual Review Rate**: % requiring human check

---

## 🔗 Related Prompts

- `detection/yolo.prompt.md` - Vehicle detection trước khi OCR
- `detection/violations.prompt.md` - Dùng plate text để log violations
- `database/schema.prompt.md` - Schema lưu plate text
- `workflows/bug-fix.prompt.md` - Debug OCR issues
