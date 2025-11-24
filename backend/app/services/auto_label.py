# backend/app/services/auto_label.py
import os
import cv2
import json
import numpy as np

# Paths (relative to backend working dir)
CACHE_DIR = os.path.join("data", "cache")
FINAL_IMG_DIR = os.path.join("data", "user_object", "images")
FINAL_LABEL_DIR = os.path.join("data", "user_object", "labels")
LOW_CONF_FILE = os.path.join("data", "user_object", "low_conf.json")

# Parameters / thresholds
MIN_AREA_RATIO = 0.01   # if contour area < 1% of image area => low confidence
EDGE_MARGIN_RATIO = 0.98  # if bbox touches nearly full image (>=98%) => low confidence

def ensure_dirs():
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs(FINAL_IMG_DIR, exist_ok=True)
    os.makedirs(FINAL_LABEL_DIR, exist_ok=True)

def _to_yolo_format(x, y, w, h, img_w, img_h):
    xc = (x + w/2) / img_w
    yc = (y + h/2) / img_h
    nw = w / img_w
    nh = h / img_h
    return xc, yc, nw, nh

def contour_auto_label(image_path):
    """
    Returns: (success:bool, label_line:str or reason:str, bbox_px:tuple)
    label_line = "0 xc yc w h" (YOLO normalized) if success
    """
    img = cv2.imread(image_path)
    if img is None:
        return False, "cannot_read_image", None

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)

    # Adaptive thresholding to be robust to lighting
    thresh = cv2.adaptiveThreshold(blur, 255,
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Morphology to reduce noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    cnts, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return False, "no_contours_found", None

    # pick largest contour
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    c = cnts[0]
    area = cv2.contourArea(c)
    bbox = cv2.boundingRect(c)  # x,y,w,h

    # Heuristics for confidence
    img_area = h * w
    area_ratio = area / max(1, img_area)
    x, y, bw, bh = bbox
    touches_edge = (x <= 1 or y <= 1 or (x + bw) >= (w-1) or (y + bh) >= (h-1))
    big_bbox_ratio = ((bw * bh) / max(1, img_area)) >= EDGE_MARGIN_RATIO

    # Low confidence if contour too small or bbox touches edges or bbox occupies almost full image
    if area_ratio < MIN_AREA_RATIO:
        return False, "small_contour", bbox
    if big_bbox_ratio or touches_edge:
        return False, "bbox_touches_edge_or_full", bbox

    # Convert to yolo normalized
    xc, yc, nw, nh = _to_yolo_format(x, y, bw, bh, w, h)
    label_line = f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}"
    return True, label_line, bbox

def save_label_and_move(image_filename, label_line):
    """
    Saves label to FINAL_LABEL_DIR and moves image to FINAL_IMG_DIR.
    Returns dict with status info.
    """
    ensure_dirs()
    src_img = os.path.join(CACHE_DIR, image_filename)
    name, _ = os.path.splitext(image_filename)
    label_path = os.path.join(FINAL_LABEL_DIR, f"{name}.txt")
    dst_img = os.path.join(FINAL_IMG_DIR, image_filename)
    # write label
    with open(label_path, "w") as f:
        f.write(label_line + "\n")
    # move image
    os.replace(src_img, dst_img)
    return {"image": image_filename, "label": os.path.basename(label_path)}

def mark_low_conf(image_filename, reason, bbox=None):
    """
    Record low confidence cases in a JSON for manual correction UI to pick up.
    """
    ensure_dirs()
    record = {"image": image_filename, "reason": reason, "bbox_px": bbox}
    data = []
    if os.path.exists(LOW_CONF_FILE):
        try:
            with open(LOW_CONF_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
    data.append(record)
    with open(LOW_CONF_FILE, "w") as f:
        json.dump(data, f, indent=2)
    # Move the image to same final images folder so manual UI can fetch it
    src_img = os.path.join(CACHE_DIR, image_filename)
    dst_img = os.path.join(FINAL_IMG_DIR, image_filename)
    if os.path.exists(src_img):
        os.replace(src_img, dst_img)
    return record

def run_auto_label_all():
    """
    Iterate through all images in CACHE_DIR and auto-label them.
    Returns summary dict with successes and low_conf list.
    """
    ensure_dirs()
    results = {"success": [], "low_conf": [], "errors": []}
    for fname in os.listdir(CACHE_DIR):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            try:
                path = os.path.join(CACHE_DIR, fname)
                ok, info, bbox = contour_auto_label(path)
                if ok:
                    saved = save_label_and_move(fname, info)
                    results["success"].append(saved)
                else:
                    rec = mark_low_conf(fname, info, bbox)
                    results["low_conf"].append(rec)
            except Exception as e:
                results["errors"].append({"image": fname, "error": str(e)})
    return results

def auto_label_images(image_dir, label_dir):
    """
    Auto-label ALL images in image_dir and write YOLO txt labels to label_dir.
    Does NOT move images or modify final dataset folders.
    Returns a list of low-confidence image names.
    """

    os.makedirs(label_dir, exist_ok=True)
    low_conf = []

    for fname in os.listdir(image_dir):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(image_dir, fname)

            ok, info, bbox = contour_auto_label(img_path)

            name, _ = os.path.splitext(fname)
            label_path = os.path.join(label_dir, f"{name}.txt")

            if ok:
                # Write YOLO normalized label for training
                with open(label_path, "w") as f:
                    f.write(info + "\n")
            else:
                # Record low confidence
                low_conf.append({
                    "image": fname,
                    "reason": info,
                    "bbox_px": bbox
                })

    return low_conf
