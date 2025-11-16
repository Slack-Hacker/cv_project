from ultralytics import YOLO
import cv2
import os
import json
import numpy as np

MODEL_PATH = "app/model/best.pt"
REF_AREA_PATH = "data/user_object/reference_area.json"

# Load YOLO model once
model = YOLO(MODEL_PATH)

# Load reference area
with open(REF_AREA_PATH, "r") as f:
    REF_AREA = json.load(f)["reference_area_norm"]

VISIBILITY_THRESHOLD = 0.30    # 30% rule


# ---------------------------------------------------------
# STEP 1: Detection on a normal image
# ---------------------------------------------------------
def detect_object(image_path):
    results = model.predict(image_path, conf=0.25, imgsz=640)
    boxes = results[0].boxes

    # If nothing detected
    if len(boxes) == 0:
        return {"detected": False, "reason": "no_detections"}

    # Use the first detected box
    box = boxes[0]
    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())

    img = cv2.imread(image_path)
    H, W = img.shape[:2]

    w = x2 - x1
    h = y2 - y1

    # Normalized area
    area_norm = (w / W) * (h / H)

    # Visibility check
    visible = area_norm >= REF_AREA * VISIBILITY_THRESHOLD

    # 3x3 region calculation
    xc = (x1 + x2) / 2
    yc = (y1 + y2) / 2

    col = min(int((xc / W) * 3), 2)
    row = min(int((yc / H) * 3), 2)

    grid_map = {
        (0,0): "top-left", (0,1): "top-center", (0,2): "top-right",
        (1,0): "middle-left", (1,1): "middle-center", (1,2): "middle-right",
        (2,0): "bottom-left", (2,1): "bottom-center", (2,2): "bottom-right"
    }

    region = grid_map[(row, col)]

    return {
        "detected": True,
        "visible_30_percent": visible,
        "region": region,
        "bbox_px": [x1, y1, x2, y2],
        "area_norm": area_norm,
        "reference_area": REF_AREA
    }


# ---------------------------------------------------------
# STEP 2: Detect from IP Webcam (single frame)
# ---------------------------------------------------------
def detect_from_stream(stream_url):
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        return {"error": "cannot_open_stream"}

    success, frame = cap.read()
    if not success:
        return {"error": "cannot_read_frame"}

    os.makedirs("data/stream_cache/", exist_ok=True)
    temp_path = "data/stream_cache/frame.jpg"
    cv2.imwrite(temp_path, frame)

    result = detect_object(temp_path)
    return result
