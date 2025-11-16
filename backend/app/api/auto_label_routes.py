# backend/app/api/auto_label_routes.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services.auto_label import run_auto_label_all, LOW_CONF_FILE, FINAL_IMG_DIR
import os

router = APIRouter()

@router.post("/auto_label/run")
def run_auto_label():
    """
    Run auto-label on all images in data/cache/.
    """
    results = run_auto_label_all()
    return JSONResponse({"status": "completed", "results": results})

@router.get("/auto_label/low_conf")
def get_low_conf_list():
    """
    Returns list of low confidence images and reasons.
    Images will be in data/user_object/images/ (moved there by auto label).
    """
    if os.path.exists(LOW_CONF_FILE):
        import json
        with open(LOW_CONF_FILE, "r") as f:
            data = json.load(f)
    else:
        data = []
    # attach file path for frontend
    for d in data:
        d["image_url"] = os.path.join("/", FINAL_IMG_DIR.replace("\\","/"), d["image"])
    return JSONResponse({"low_conf": data})
