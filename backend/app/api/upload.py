import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

CACHE_DIR = "data/cache/"

@router.post("/upload")
async def upload_images(files: list[UploadFile] = File(...)):
    
    # Validation
    allowed_ext = ["jpg", "jpeg", "png"]
    
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved_files = []

    for file in files:
        ext = file.filename.split(".")[-1].lower()
        if ext not in allowed_ext:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")

        save_path = os.path.join(CACHE_DIR, file.filename)

        # Save to cache
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_files.append(file.filename)

    return JSONResponse({
        "status": "success",
        "files_saved": saved_files,
        "folder": CACHE_DIR
    })
