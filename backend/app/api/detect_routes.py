# backend/app/api/detect_routes.py

from fastapi import APIRouter, UploadFile, File, Query
import os
from app.services.detect import detect_object, detect_from_stream

router = APIRouter()

# ============================================================
# 1) Detect object from uploaded image
# ============================================================
@router.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    folder = "data/detect_input/"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, file.filename)

    # Save uploaded file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Run YOLO detection
    result = detect_object(file_path)

    return {
        "status": "ok",
        "file": file.filename,
        "result": result
    }


# ============================================================
# 2) Detect object from IP Webcam (single frame)
# Used by LiveDetection.tsx
# ============================================================
@router.get("/detect/stream")
def detect_stream(url: str = Query(..., description="IP webcam MJPEG URL")):
    """
    Example:
    /detect/stream?url=http://192.168.x.x:8080/video
    """
    result = detect_from_stream(url)

    return {
        "status": "ok",
        "stream": url,
        "result": result
    }
