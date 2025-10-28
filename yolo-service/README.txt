YOLO Detection Service
======================

Handles 2 models:
1. Vehicle Detection (best1.pt)
2. License Plate OCR (license_plate.pt)

Deploy:
-------
./deploy-yolo.sh

Endpoints:
----------
GET  /health               - Health check
POST /detect/vehicle       - Detect vehicles/plates/helmets/lights
POST /detect/plate         - OCR license plate

Port: 8001

Test:
-----
curl http://localhost:8001/health

Config:
-------
Environment:
  VEHICLE_MODEL_PATH=/app/models/best1.pt
  PLATE_MODEL_PATH=/app/models/license_plate.pt

Backend config (server.yaml):
  services:
    yolo_api: "http://IP:8001"
