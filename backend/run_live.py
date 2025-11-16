# backend/run_live.py
from app.services.detect import detect_stream_live

if __name__ == "__main__":
    # Replace with your phone IP / port
    stream_url = "http://192.168.1.8:8080/video"
    # tune these parameters if needed
    detect_stream_live(stream_url, conf=0.15, imgsz=640, frame_skip=2, max_fps=8, show_window=True)
