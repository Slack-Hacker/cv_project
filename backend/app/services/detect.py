import os
import json
import cv2
import numpy as np
from ultralytics import YOLO

# =====================================================================
# CONFIG
# =====================================================================
MODEL_PATH = "app/model/best.pt"        # user-trained custom model
DEFAULT_MODEL_WEIGHTS = "yolov8m.pt"    # pretrained COCO model
REF_AREA_PATH = "data/user_object/reference_area.json"

DEFAULT_REF_AREA = 0.05
VISIBILITY_THRESHOLD = 0.30             # 30% visibility rule

# =====================================================================
# LOAD MODELS (custom + default)
# =====================================================================
print("\n=================== MODEL LOADING ===================")

custom_model = None
default_model = None

# -------- Load custom model (if exists) --------
if os.path.exists(MODEL_PATH):
    try:
        custom_model = YOLO(MODEL_PATH)
        print("✔ Loaded CUSTOM model:", MODEL_PATH)
    except Exception as e:
        print("❌ Failed loading custom model:", e)
else:
    print("⚠ Custom model not found:", MODEL_PATH)

# -------- Load default pretrained model --------
try:
    default_model = YOLO(DEFAULT_MODEL_WEIGHTS)
    print("✔ Loaded DEFAULT model:", DEFAULT_MODEL_WEIGHTS)
except Exception as e:
    print("❌ Failed loading default YOLO model:", e)

print("====================================================\n")


def reload_model():
    """Reload custom model after training."""
    global custom_model
    if os.path.exists(MODEL_PATH):
        custom_model = YOLO(MODEL_PATH)
        print("✔ Custom model reloaded")
        return True
    return False


# =====================================================================
# LOAD REFERENCE AREA (median normalized area)
# =====================================================================
if os.path.exists(REF_AREA_PATH):
    try:
        with open(REF_AREA_PATH, "r") as f:
            REF_AREA = json.load(f)["reference_area_norm"]
    except:
        REF_AREA = DEFAULT_REF_AREA
else:
    REF_AREA = DEFAULT_REF_AREA


# =====================================================================
# GRID + REGION MAPPING HELPERS
# =====================================================================
def compute_3x3_regions(W, H):
    """Return list of 9 regions inside a 9×9 grid."""
    cell_w = W / 9
    cell_h = H / 9

    regions = []
    for r in range(0, 9, 3):
        for c in range(0, 9, 3):
            x1 = int(c * cell_w)
            y1 = int(r * cell_h)
            x2 = int((c + 3) * cell_w)
            y2 = int((r + 3) * cell_h)
            regions.append((x1, y1, x2, y2))

    return regions


def intersection_area(b, r):
    xa = max(b[0], r[0])
    ya = max(b[1], r[1])
    xb = min(b[2], r[2])
    yb = min(b[3], r[3])
    return max(0, xb - xa) * max(0, yb - ya)


# =====================================================================
# PROCESS YOLO RESULTS
# =====================================================================
def extract_boxes(result):
    """Convert YOLO result into list of dict boxes."""
    out = []
    if result is None:
        return out
    if len(result.boxes) == 0:
        return out

    names = result.names

    for b in result.boxes:
        xyxy = b.xyxy[0].cpu().numpy().astype(int).tolist()
        conf = float(b.conf[0])
        cls_id = int(b.cls[0])

        out.append({
            "xyxy": xyxy,
            "conf": conf,
            "cls": cls_id,
            "name": names.get(cls_id, "object")
        })

    return out


# =====================================================================
# MAIN DETECT FUNCTION (MERGED MODELS)
# =====================================================================
def detect_object(image_path, conf_thresh=0.25, iou_thresh=0.45):
    """
    Runs detection using:
       ✔ your custom model  (best.pt)
       ✔ pretrained COCO model (yolov8m.pt)
    Merges detections and returns BEST object.
    """

    img = cv2.imread(image_path)
    if img is None:
        return {"detected": False, "error": "cannot_read_image"}

    H, W = img.shape[:2]

    all_dets = []

    # -------------------- CUSTOM MODEL --------------------
    if custom_model:
        try:
            r = custom_model.predict(image_path, conf=conf_thresh, iou=iou_thresh)
            all_dets += extract_boxes(r[0])
        except Exception as e:
            print("⚠ Custom model error:", e)

    # -------------------- DEFAULT YOLO --------------------
    if default_model:
        try:
            r2 = default_model.predict(image_path, conf=conf_thresh, iou=iou_thresh)
            all_dets += extract_boxes(r2[0])
        except Exception as e:
            print("⚠ Default model error:", e)

    # -------------------- NO DETECTIONS --------------------
    if len(all_dets) == 0:
        return {"detected": False, "reason": "no_detections"}

    # -------------------- PICK BEST OBJECT --------------------
    # If custom model has ANY detection → give priority
    custom_names = set()

    if custom_model:
        try:
            # Collect custom class names dynamically
            tmp = YOLO(MODEL_PATH)
            for n in tmp.names.values():
                custom_names.add(n)
        except:
            pass

    # Filter detections belonging to custom class
    custom_hits = [d for d in all_dets if d["name"] in custom_names]

    if len(custom_hits) > 0:
        best = max(custom_hits, key=lambda x: x["conf"])
    else:
        best = max(all_dets, key=lambda x: x["conf"])

    x1, y1, x2, y2 = best["xyxy"]

    w = x2 - x1
    h = y2 - y1
    area_norm = (w / W) * (h / H)
    visible = area_norm >= (REF_AREA * VISIBILITY_THRESHOLD)

    # -------------------- REGION MAPPING --------------------
    regions = compute_3x3_regions(W, H)
    region_name = "unknown"
    region_id = 0

    box_area = max(1, w * h)

    for i, reg in enumerate(regions):
        if intersection_area((x1, y1, x2, y2), reg) / box_area >= 0.50:
            region_name = f"place{i+1}"
            region_id = i + 1
            break

    # -------------------- RETURN RESULT --------------------
    return {
        "detected": True,
        "class_name": best["name"],
        "bbox_px": [x1, y1, x2, y2],
        "conf": best["conf"],
        "visible_30_percent": visible,
        "area_norm": area_norm,
        "reference_area": REF_AREA,
        "region": region_name,
        "region_id": region_id,
        "region_boxes": regions,
        "grid_type": "9x9 → 3x3 mapping"
    }


# =====================================================================
# STREAM DETECTION
# =====================================================================
def detect_from_stream(url, conf=0.25, imgsz=640):
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        return {"error": "cannot_open_stream"}

    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        return {"error": "cannot_read_frame"}

    os.makedirs("data/stream_cache", exist_ok=True)
    temp = "data/stream_cache/frame.jpg"
    cv2.imwrite(temp, frame)

    return detect_object(temp, conf_thresh=conf)
