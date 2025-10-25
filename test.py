
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time video detection with Ultralytics YOLO.
Usage examples:
  python yolo_rt_detect.py --model path/to/yolo.pt --source path/to/video.mp4
  python yolo_rt_detect.py --model yolo.pt --source 0                # webcam
  python yolo_rt_detect.py --model yolo.pt --source rtsp://....      # RTSP stream
  python yolo_rt_detect.py --model yolo.pt --source video.mp4 --width 960 --save

Requirements:
  pip install ultralytics opencv-python
"""
import argparse
import time
import sys
from pathlib import Path

import cv2
import numpy as np

# Try to import Ultralytics
try:
    from ultralytics import YOLO
    import torch
except Exception as e:
    print("❌ Lỗi: Không import được 'ultralytics'. Hãy cài đặt trước:\n"
          "    pip install ultralytics opencv-python\n"
          f"Chi tiết: {e}")
    sys.exit(1)


def parse_args():
    p = argparse.ArgumentParser(description="Real-time YOLO detection (Ultralytics)")
    p.add_argument("--model", type=str, required=True, help="Đường dẫn model .pt/.onnx/.engine")
    p.add_argument("--source", type=str, required=True,
                   help="Đường dẫn video/stream hoặc index webcam (vd: 0)")
    p.add_argument("--conf", type=float, default=0.25, help="Ngưỡng confidence")
    p.add_argument("--iou", type=float, default=0.45, help="Ngưỡng IOU NMS")
    p.add_argument("--width", type=int, default=0, help="Resize theo chiều rộng (0 = giữ nguyên)")
    p.add_argument("--device", type=str, default="", help="Thiết bị: ''=auto, 'cpu' hoặc '0','0,1'")
    p.add_argument("--save", action="store_true", help="Lưu video output")
    p.add_argument("--out", type=str, default="", help="Tên file output (mặc định tự sinh)")
    p.add_argument("--show", action="store_true", help="Hiển thị cửa sổ (mặc định bật nếu có GUI)")
    return p.parse_args()


def open_source(src_str: str):
    """OpenCV VideoCapture for file/stream/webcam; return cap and a flag is_webcam."""
    is_webcam = False
    # If source is a pure integer string, treat as webcam index
    if src_str.isdigit():
        cap = cv2.VideoCapture(int(src_str))
        is_webcam = True
    else:
        cap = cv2.VideoCapture(src_str)
    if not cap.isOpened():
        raise RuntimeError(f"Không mở được nguồn video: {src_str}")
    return cap, is_webcam


def get_fps_width_height(cap):
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0 or np.isnan(fps):
        fps = 0.0  # unknown fps
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return fps, w, h


def maybe_resize(frame, target_width):
    if target_width and target_width > 0 and frame.shape[1] != target_width:
        r = target_width / float(frame.shape[1])
        new_h = int(round(frame.shape[0] * r))
        frame = cv2.resize(frame, (target_width, new_h), interpolation=cv2.INTER_LINEAR)
    return frame


def put_hud(img, text, org=(8, 24)):
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)


def main():
    args = parse_args()

    # Device selection
    if args.device.lower() == "cpu":
        device = "cpu"
    else:
        device = args.device if args.device else ( "cuda" if torch.cuda.is_available() else "cpu" )

    # Load model
    try:
        model = YOLO(args.model)
    except Exception as e:
        print(f"❌ Lỗi load model '{args.model}': {e}")
        sys.exit(1)

    # Open source
    cap, is_webcam = open_source(args.source)
    src_fps, src_w, src_h = get_fps_width_height(cap)

    # Prepare writer
    writer = None
    out_path = None
    if args.save:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_name = args.out if args.out else f"out_{Path(args.source).stem if not is_webcam else 'webcam'}.mp4"
        out_path = str(Path(out_name).resolve())
        # Determine output size after optional resize
        tmp_frame_ok, tmp_frame = cap.read()
        if not tmp_frame_ok:
            print("❌ Không đọc được frame đầu tiên để cấu hình ghi video.")
            sys.exit(1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # rewind if file
        vis0 = maybe_resize(tmp_frame, args.width)
        out_size = (vis0.shape[1], vis0.shape[0])
        out_fps = src_fps if src_fps > 0 else 25.0
        writer = cv2.VideoWriter(out_path, fourcc, out_fps, out_size)

    # Window
    show = args.show or True  # show by default if environment supports GUI
    win_name = "YOLO Real-Time"
    if show:
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_EXPANDED)

    # Inference loop (stream=True yields generator of results, but we do manual loop for flexibility)
    prev_t = time.time()
    frame_count = 0
    smooth_fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = maybe_resize(frame, args.width)

        # Run detection; set verbose False to reduce logs
        results = model.predict(
            source=frame,
            conf=args.conf,
            iou=args.iou,
            device=device,
            verbose=False
        )

        # Ultralytics returns a list; take first
        res = results[0]
        # Draw annotations using built-in plot()
        vis = res.plot()

        # FPS calc (EMA for smoothness)
        now = time.time()
        dt = now - prev_t
        prev_t = now
        inst_fps = 1.0 / dt if dt > 0 else 0.0
        alpha = 0.1
        smooth_fps = (1 - alpha) * smooth_fps + alpha * inst_fps if frame_count > 0 else inst_fps
        frame_count += 1

        # HUD text
        info = f"Device: {device} | FPS: {smooth_fps:5.1f} | {args.model} | conf={args.conf} iou={args.iou}"
        put_hud(vis, info, (8, 28))

        # Show
        if show:
            cv2.imshow(win_name, vis)
            # If FPS known, wait accordingly; else minimal delay
            delay = 1 if src_fps <= 0 else max(1, int(1000.0 / src_fps))
            if cv2.waitKey(delay) & 0xFF == ord('q'):
                break

        # Save
        if writer is not None:
            writer.write(vis)

    cap.release()
    if writer is not None:
        writer.release()
        print(f"💾 Đã lưu video output: {out_path}")
    if show:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass