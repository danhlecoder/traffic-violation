#!/usr/bin/env python3
"""
Speed Calibration Tool - Đo pixels_per_meter để chuyển đổi px/s → km/h

Cách sử dụng:
1. Chụp 1 frame từ camera
2. Đo khoảng cách thực tế trên đường (ví dụ: 5 mét)
3. Đo khoảng cách tương ứng trên ảnh (pixels)
4. Tính pixels_per_meter = pixels / meters

Ví dụ:
    python tools/calibrate_speed.py --image frame.jpg
"""

import cv2
import argparse
import sys
from pathlib import Path


class SpeedCalibrator:
    """Tool để calibrate speed measurement"""

    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image = None
        self.points = []
        self.scale_factor = 1.0

    def load_image(self) -> bool:
        """Load ảnh"""
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            print(f"❌ Không thể đọc ảnh: {self.image_path}")
            return False

        # Resize nếu ảnh quá lớn
        h, w = self.image.shape[:2]
        max_width = 1280
        if w > max_width:
            self.scale_factor = max_width / w
            new_h = int(h * self.scale_factor)
            self.image = cv2.resize(self.image, (max_width, new_h))
            print(f"📏 Ảnh đã resize: {w}x{h} → {max_width}x{new_h}")

        return True

    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback để chọn 2 điểm"""
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points) < 2:
                # Scale back to original size
                orig_x = int(x / self.scale_factor)
                orig_y = int(y / self.scale_factor)
                self.points.append((orig_x, orig_y))
                print(f"✓ Điểm {len(self.points)}: ({orig_x}, {orig_y})")

    def draw_points(self):
        """Vẽ các điểm đã chọn"""
        display_image = self.image.copy()

        # Vẽ các điểm
        for i, (x, y) in enumerate(self.points):
            # Scale to display size
            disp_x = int(x * self.scale_factor)
            disp_y = int(y * self.scale_factor)

            cv2.circle(display_image, (disp_x, disp_y), 8, (0, 0, 255), -1)
            cv2.putText(
                display_image,
                f"P{i+1}",
                (disp_x + 10, disp_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )

        # Vẽ đường nối
        if len(self.points) == 2:
            p1 = (int(self.points[0][0] * self.scale_factor),
                  int(self.points[0][1] * self.scale_factor))
            p2 = (int(self.points[1][0] * self.scale_factor),
                  int(self.points[1][1] * self.scale_factor))
            cv2.line(display_image, p1, p2, (0, 255, 0), 2)

            # Tính khoảng cách pixels
            dx = self.points[1][0] - self.points[0][0]
            dy = self.points[1][1] - self.points[0][1]
            distance_px = (dx**2 + dy**2)**0.5

            # Hiển thị khoảng cách
            mid_x = int((p1[0] + p2[0]) / 2)
            mid_y = int((p1[1] + p2[1]) / 2)
            cv2.putText(
                display_image,
                f"{distance_px:.1f} pixels",
                (mid_x, mid_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

        return display_image

    def run(self):
        """Chạy calibration"""
        if not self.load_image():
            return

        print("\n" + "="*60)
        print("🎯 SPEED CALIBRATION TOOL")
        print("="*60)
        print("\nHƯỚNG DẪN:")
        print("1. Click 2 điểm trên ảnh để tạo đường đo")
        print("2. Đo khoảng cách thực tế giữa 2 điểm đó (mét)")
        print("3. Nhập khoảng cách thực tế để tính calibration")
        print("\nPhím tắt:")
        print("  - 'r': Reset (chọn lại 2 điểm)")
        print("  - 'q': Thoát")
        print("="*60 + "\n")

        cv2.namedWindow("Calibration")
        cv2.setMouseCallback("Calibration", self.mouse_callback)

        while True:
            display_image = self.draw_points()
            cv2.imshow("Calibration", display_image)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            elif key == ord('r'):
                self.points = []
                print("\n🔄 Reset - chọn lại 2 điểm")
            elif key == 13 and len(self.points) == 2:  # Enter
                self.calculate_calibration()

        cv2.destroyAllWindows()

    def calculate_calibration(self):
        """Tính toán calibration"""
        if len(self.points) != 2:
            print("❌ Cần chọn đủ 2 điểm!")
            return

        # Tính khoảng cách pixels
        dx = self.points[1][0] - self.points[0][0]
        dy = self.points[1][1] - self.points[0][1]
        distance_px = (dx**2 + dy**2)**0.5

        print(f"\n📏 Khoảng cách đo được: {distance_px:.1f} pixels")

        # Nhập khoảng cách thực tế
        try:
            real_distance_m = float(input("📍 Nhập khoảng cách thực tế (mét): "))

            if real_distance_m <= 0:
                print("❌ Khoảng cách phải > 0")
                return

            # Tính calibration
            pixels_per_meter = distance_px / real_distance_m

            print("\n" + "="*60)
            print("✅ KẾT QUẢ CALIBRATION")
            print("="*60)
            print(f"Khoảng cách pixels: {distance_px:.1f} px")
            print(f"Khoảng cách thực tế: {real_distance_m:.1f} m")
            print(f"\n📊 PIXELS_PER_METER = {pixels_per_meter:.2f}")
            print("="*60)

            # Ví dụ chuyển đổi
            print("\n💡 VÍ DỤ CHUYỂN ĐỔI:")
            for speed_px_s in [10, 20, 50, 100]:
                speed_m_s = speed_px_s / pixels_per_meter
                speed_kmh = speed_m_s * 3.6
                print(f"  {speed_px_s:3d} px/s  →  {speed_kmh:5.1f} km/h")

            print("\n📝 CẬP NHẬT FILE .env:")
            print(f"TRAJECTORY_PIXELS_PER_METER={pixels_per_meter:.2f}")
            print("="*60 + "\n")

        except ValueError:
            print("❌ Giá trị không hợp lệ!")
        except KeyboardInterrupt:
            print("\n\n⏹️ Hủy calibration")


def main():
    parser = argparse.ArgumentParser(
        description="Speed Calibration Tool - Đo pixels_per_meter"
    )
    parser.add_argument(
        "--image",
        "-i",
        required=True,
        help="Đường dẫn đến ảnh frame từ camera"
    )

    args = parser.parse_args()

    if not Path(args.image).exists():
        print(f"❌ File không tồn tại: {args.image}")
        sys.exit(1)

    calibrator = SpeedCalibrator(args.image)
    calibrator.run()


if __name__ == "__main__":
    main()
