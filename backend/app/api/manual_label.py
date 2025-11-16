from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

FINAL_IMG_DIR = "data/user_object/images/"
FINAL_LABEL_DIR = "data/user_object/labels/"

class ManualLabel(BaseModel):
    image: str
    x1: int
    y1: int
    x2: int
    y2: int
    img_w: int
    img_h: int

router = APIRouter()

@router.post("/label/manual")
def manual_label(data: ManualLabel):

    img_path = os.path.join(FINAL_IMG_DIR, data.image)
    if not os.path.exists(img_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # Normalize to YOLO format
    x = min(data.x1, data.x2)
    y = min(data.y1, data.y2)
    w = abs(data.x2 - data.x1)
    h = abs(data.y2 - data.y1)

    xc = (x + w/2) / data.img_w
    yc = (y + h/2) / data.img_h
    nw = w / data.img_w
    nh = h / data.img_h

    label_line = f"0 {xc:.6f} {yc:.6f} {nw:.6f} {nh:.6f}"

    name = data.image.split(".")[0]
    label_path = os.path.join(FINAL_LABEL_DIR, name + ".txt")

    with open(label_path, "w") as f:
        f.write(label_line)

    return {"status": "saved", "label_file": name + ".txt"}
