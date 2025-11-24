# backend/app/api/train_routes.py

import os
import shutil
import threading
import time
import json
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from pathlib import Path
import subprocess
import traceback
import cv2

# per-image contour labeler (returns ok,label_or_reason,bbox)
from app.services.auto_label import contour_auto_label
from app.services.detect import reload_model

router = APIRouter()

# ---------------- PATHS ----------------

TRAIN_TMP = os.path.join("data", "train_tmp")
IMAGES_TMP = os.path.join(TRAIN_TMP, "images")
LABELS_TMP = os.path.join(TRAIN_TMP, "labels")
DATA_YAML = os.path.join(TRAIN_TMP, "data.yaml")
STATUS_FILE = os.path.join(TRAIN_TMP, "train_status.json")

os.makedirs(IMAGES_TMP, exist_ok=True)
os.makedirs(LABELS_TMP, exist_ok=True)

# ---------------- GLOBAL STATE ----------------

training_state = {
    # Training
    "running": False,
    "progress": 0,            # 0-100
    "status": "idle",
    "log": [],
    "last_run": None,
    "error": None,

    # Upload + auto-label
    "upload_phase": "idle",          # idle | uploading | auto-labeling | done | failed
    "upload_total": 0,
    "upload_processed": 0,
    "upload_current": None,
    "upload_errors": [],
    "upload_percent": 0
}

def save_status():
    # ensure folder exists
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(training_state, f, indent=2)
    except Exception:
        print("WARN: failed to write status file:", STATUS_FILE)
        traceback.print_exc()


# ------------------ UTIL: auto-fix bbox ------------------

def _clamp_and_shrink_bbox(bbox, img_w, img_h):
    """
    bbox: (x,y,w,h) in px returned by contour_auto_label or None
    Return YOLO normalized line "0 xc yc w h"
    Strategy:
     - If bbox provided, clamp to image boundary with a small margin and, if it's huge,
       shrink it by 10% margin (to avoid near-full image boxes).
     - If bbox is None, fallback to center 30% box.
    """
    if bbox is None:
        # fallback central box (30% width & height)
        w = int(img_w * 0.30)
        h = int(img_h * 0.30)
        x = int((img_w - w) / 2)
        y = int((img_h - h) / 2)
    else:
        x, y, w, h = bbox
        # clamp within image
        x = max(1, min(x, img_w - 2))
        y = max(1, min(y, img_h - 2))
        w = max(2, min(w, img_w - x - 1))
        h = max(2, min(h, img_h - y - 1))

        # if bbox occupies >90% area, shrink by 10% margin
        area_ratio = (w * h) / max(1, (img_w * img_h))
        if area_ratio > 0.9:
            reduce_w = int(w * 0.08)
            reduce_h = int(h * 0.08)
            x += reduce_w // 2
            y += reduce_h // 2
            w = max(2, w - reduce_w)
            h = max(2, h - reduce_h)

        # small safety margins: ensure inside
        x = max(1, min(x, img_w - w - 1))
        y = max(1, min(y, img_h - h - 1))

    xc = (x + w / 2) / img_w
    yc = (y + h / 2) / img_h
    nw = w / img_w
    nh = h / img_h

    return f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}"


# ============================================================
#                 UPLOAD IMAGES → BACKGROUND AUTO LABEL
# ============================================================

@router.post("/train/upload")
async def upload_train_images(
    label: str = File(...),
    files: List[UploadFile] = File(...)
):

    if training_state["running"]:
        raise HTTPException(status_code=409, detail="Training already running")

    # Reset upload state
    training_state.update({
        "upload_phase": "uploading",
        "upload_total": len(files),
        "upload_processed": 0,
        "upload_current": None,
        "upload_errors": [],
        "upload_percent": 0,
        "status": "uploading",
        "label": label.strip()
    })
    save_status()

    # Clear training temp folder
    for p in [IMAGES_TMP, LABELS_TMP]:
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p, exist_ok=True)

    # Ensure manual label folder exists
    USER_IMG_DIR = "data/user_object/images/"
    os.makedirs(USER_IMG_DIR, exist_ok=True)

    saved_names = []

    for f in files:
        img_bytes = await f.read()

        # 1️⃣ Save to train_tmp/images
        train_path = os.path.join(IMAGES_TMP, f.filename)
        with open(train_path, "wb") as out:
            out.write(img_bytes)

        # 2️⃣ Save to user_object/images
        user_path = os.path.join(USER_IMG_DIR, f.filename)
        with open(user_path, "wb") as out2:
            out2.write(img_bytes)

        saved_names.append(f.filename)

    # Start auto-label thread
    def _thread_starter():
        try:
            _auto_label_thread()
        except Exception as e:
            training_state["upload_phase"] = "failed"
            training_state["upload_errors"].append({"error": str(e)})
            save_status()

    threading.Thread(target=_thread_starter, daemon=True).start()

    return {"status": "started", "saved": saved_names}



def _auto_label_thread():
    """
    Runs in background: iterates images in IMAGES_TMP, runs contour_auto_label on each,
    writes YOLO txt labels to LABELS_TMP, updates training_state.upload_* fields and percent.
    Auto-fixes bad bboxes so YOLO has labels for all images.
    """
    print("DEBUG: _auto_label_thread invoked")
    training_state["upload_phase"] = "auto-labeling"
    save_status()

    try:
        imgs = [f for f in os.listdir(IMAGES_TMP)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    except Exception as e:
        print("ERROR: cannot list IMAGES_TMP:", IMAGES_TMP, repr(e))
        traceback.print_exc()
        training_state["upload_phase"] = "failed"
        training_state["upload_errors"].append({"error": str(e)})
        save_status()
        return

    print("DEBUG: files in IMAGES_TMP:", imgs)
    total = len(imgs)
    training_state["upload_total"] = total
    training_state["upload_processed"] = 0
    training_state["upload_errors"] = []
    training_state["upload_percent"] = 0
    save_status()

    for idx, fname in enumerate(imgs):
        try:
            training_state["upload_current"] = fname
            save_status()

            img_path = os.path.join(IMAGES_TMP, fname)
            label_path = os.path.join(LABELS_TMP, fname.rsplit(".", 1)[0] + ".txt")
            
            # 1️⃣ If manual label exists → use it directly and skip auto-label
            manual_label_path = os.path.join(
                "data/user_object/labels",
                fname.rsplit(".", 1)[0] + ".txt"
            )

            if os.path.exists(manual_label_path):
                shutil.copyfile(manual_label_path, label_path)
                print(f"DEBUG: Using manual label for {fname}")
                training_state["upload_errors"].append({
                    "image": fname,
                    "reason": "manual_label_used"
                })
                training_state["upload_processed"] += 1
                training_state["upload_percent"] = int((training_state["upload_processed"] / max(1, total)) * 100)
                save_status()
                continue


            print(f"DEBUG: processing image: {img_path}")
            start_t = time.time()
            ok, info, bbox = contour_auto_label(img_path)
            duration = time.time() - start_t
            print(f"DEBUG: processed {fname} - ok={ok} info={info} time={duration:.3f}s")

            # Read image dims (for auto-fix)
            img = cv2.imread(img_path)
            if img is None:
                # cannot read - record error and skip
                training_state["upload_errors"].append({"image": fname, "reason": "cannot_read_image"})
            else:
                h, w = img.shape[:2]

                if ok:
                    # info contains YOLO label line already
                    try:
                        with open(label_path, "w", encoding="utf-8") as f:
                            f.write(info + "\n")
                    except Exception as e:
                        print(f"ERROR: writing label for {fname}: {e}")
                        training_state["upload_errors"].append({"image": fname, "error": str(e)})
                else:
                    # Auto-fix: use returned bbox if present, else fallback central box
                    try:
                        fixed_label = _clamp_and_shrink_bbox(bbox, w, h)
                        with open(label_path, "w", encoding="utf-8") as f:
                            f.write(fixed_label + "\n")
                        # Record that we auto-fixed this image (helpful for UI)
                        training_state["upload_errors"].append({
                            "image": fname,
                            "reason": f"auto_fixed:{info}"
                        })
                        print(f"DEBUG: auto-fixed label for {fname}: {fixed_label}")
                    except Exception as e:
                        print(f"ERROR: auto-fix failed for {fname}: {e}")
                        traceback.print_exc()
                        training_state["upload_errors"].append({"image": fname, "error": str(e)})

            # increment processed count and compute percent defensively
            training_state["upload_processed"] += 1
            total_safe = max(1, training_state.get("upload_total", total))
            training_state["upload_percent"] = int((training_state["upload_processed"] / total_safe) * 100)
            save_status()

        except Exception as e:
            print("ERROR: exception while processing", fname, repr(e))
            traceback.print_exc()
            training_state["upload_errors"].append({"image": fname, "error": str(e)})
            training_state["upload_processed"] += 1
            total_safe = max(1, training_state.get("upload_total", total))
            training_state["upload_percent"] = int((training_state["upload_processed"] / total_safe) * 100)
            save_status()
            continue

    # Write proper data.yaml (ultralytics expects valid YAML)
    try:
        train_path = os.path.abspath(IMAGES_TMP).replace("\\", "/")
        user_label = training_state.get("label", "object")

        yaml_lines = [
            f"train: {train_path}",
            f"val: {train_path}",
            "",
            f"nc: 1",
            f'names: ["{user_label}"]'
        ]

        with open(DATA_YAML, "w", encoding="utf-8") as f:
            f.write("\n".join(yaml_lines) + "\n")
        print("DEBUG: wrote data.yaml:", DATA_YAML)
    except Exception as e:
        print("ERROR: writing data.yaml:", repr(e))
        traceback.print_exc()
        training_state["upload_errors"].append({"error": str(e)})

    # finalize upload state
    training_state["upload_phase"] = "done"
    training_state["status"] = "uploaded"
    training_state["upload_current"] = None
    training_state["upload_percent"] = 100
    save_status()
    print("DEBUG: auto-label thread finished, total:", total)


@router.get("/train/upload-status")
def upload_status():
    """Frontend polls this every 500ms"""
    state = training_state
    return {
        "phase": state.get("upload_phase", "idle"),
        "total": state.get("upload_total", 0),
        "processed": state.get("upload_processed", 0),
        "current": state.get("upload_current"),
        "errors": state.get("upload_errors", []),
        "percent": int(state.get("upload_percent", 0))
    }


# ============================================================
#                      TRAINING THREAD
# ============================================================

def _train_thread(data_yaml_path, epochs=20, batch=8, imgsz=640):
    try:
        training_state.update({
            "running": True,
            "progress": 0,
            "status": "training",
            "log": []
        })
        save_status()

        run_name = f"user_custom_{int(time.time())}"
        training_state["log"].append(f"Training started: {run_name}")
        save_status()

        # Use "yolo train" CLI (ultralytics CLI)
        cmd = [
            "yolo", "train",
            f"model=yolov8n.pt",
            f"data={data_yaml_path}",
            f"name={run_name}",
            f"epochs={epochs}",
            f"batch={batch}",
            f"imgsz={imgsz}"
        ]

        print("DEBUG: training command:", " ".join(cmd))
        # open subprocess with explicit robust decoding
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",  # replace undecodable bytes rather than crash
            bufsize=1
        )

        # Read lines robustly (works on Windows)
        for raw_line in iter(proc.stdout.readline, ""):
            if not raw_line:
                break
            line = raw_line.strip()
            if line == "":
                continue
            print("TRAIN_LOG:", line)
            training_state["log"].append(line)

            # Try to parse epoch info
            if "Epoch" in line and "/" in line:
                try:
                    parts = line.split()
                    epoch_part = [p for p in parts if "/" in p][0]
                    cur, tot = epoch_part.split("/")
                    cur = int(cur)
                    tot = int(tot)
                    training_state["progress"] = int((cur / tot) * 100)
                    training_state["status"] = f"Epoch {cur}/{tot}"
                    save_status()
                except Exception:
                    pass

            save_status()

        proc.wait()

        if proc.returncode != 0:
            training_state.update({
                "status": "failed",
                "error": f"Training failed: rc={proc.returncode}",
                "running": False
            })
            save_status()
            return

        # Copy best.pt (ultralytics writes to runs/train/<name>/weights/best.pt)
        best_path_train = Path("runs") / "train" / run_name / "weights" / "best.pt"
        best_path_detect = Path("runs") / "detect" / run_name / "weights" / "best.pt"

        if best_path_train.exists():
            best_path = best_path_train
        elif best_path_detect.exists():
            best_path = best_path_detect
        else:
            training_state.update({
                "status": "failed",
                "error": "best.pt not found in train/ or detect/",
                "running": False
            })
            save_status()
            return

        if not best_path.exists():
            training_state.update({
                "status": "failed",
                "error": "best.pt not found",
                "running": False
            })
            save_status()
            return

        os.makedirs("app/model", exist_ok=True)
        try:
            shutil.copyfile(best_path, "app/model/best.pt")
        except Exception as e:
            print("ERROR: copying best.pt:", repr(e))
            training_state["log"].append(f"Error copying best.pt: {e}")
            save_status()

        # reload model in memory
        try:
            reload_model()
            training_state["log"].append("Model reloaded.")
        except Exception as e:
            print("ERROR: reload_model failed:", repr(e))
            training_state["log"].append(f"Reload failed: {e}")

        training_state.update({
            "status": "done",
            "progress": 100,
            "running": False,
            "last_run": str(best_path)
        })
        save_status()

    except Exception as e:
        print("ERROR: Exception in _train_thread:", repr(e))
        traceback.print_exc()
        training_state.update({
            "status": "failed",
            "error": str(e),
            "running": False
        })
        save_status()


@router.post("/train/start")
def start_training(epochs: int = 20, batch: int = 8, imgsz: int = 640):
    if training_state["running"]:
        raise HTTPException(409, "Training already running")

    # check at least 3 images exist
    all_imgs = [p for p in Path(IMAGES_TMP).glob("*") if p.suffix.lower() in [".jpg", ".jpeg", ".png"]]
    if len(all_imgs) < 3:
        raise HTTPException(400, "Not enough images")

    threading.Thread(
        target=_train_thread,
        args=(DATA_YAML, epochs, batch, imgsz),
        daemon=True
    ).start()

    return {"status": "started"}


@router.get("/train/status")
def train_status():
    """Frontend polls training progress."""
    return {
        "running": training_state.get("running", False),
        "progress": training_state.get("progress", 0),
        "status": training_state.get("status", "idle"),
        "error": training_state.get("error"),
        "last_run": training_state.get("last_run")
    }
