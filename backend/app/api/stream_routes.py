from fastapi import APIRouter
from app.services.detect import detect_from_stream

router = APIRouter()

@router.get("/detect/stream")
def detect_stream(url: str):
    """
    Example:
    /api/detect/stream?url=http://192.168.1.8:8080/video
    """
    result = detect_from_stream(url)
    return {"status": "ok", "result": result}
