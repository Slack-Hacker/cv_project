from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.upload import router as upload_router
from app.api.auto_label_routes import router as al_router
from app.api.manual_label import router as manual_label_router
from app.api.detect_routes import router as detect_router
from app.api.stream_routes import router as stream_router
from app.api.train_routes import router as train_router
from fastapi.middleware.cors import CORSMiddleware
from app.api.label_status import router as label_status_router
import os

app = FastAPI(title="cv1 Project Backend")

app.include_router(upload_router, prefix="/api")
app.include_router(al_router, prefix="/api")
app.include_router(manual_label_router, prefix="/api")
app.include_router(detect_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(train_router, prefix="/api")
app.include_router(label_status_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Expose user images folder so frontend can preview low-conf images
DATA_USER_IMG = os.path.join("data", "user_object", "images")
os.makedirs(DATA_USER_IMG, exist_ok=True)
app.mount("/user_images", StaticFiles(directory=DATA_USER_IMG), name="user_images")

@app.get("/")
def root():
    return {"message": "Backend running"}
