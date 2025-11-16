from fastapi import APIRouter, UploadFile, File
import os
from app.services.detect import detect_object

router = APIRouter()

@router.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    folder = "data/detect_input/"
    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    result = detect_object(file_path)

    return {"status": "ok", "file": file.filename, "result": result}
