from ultralytics import YOLO

def train():
    model = YOLO("yolov8n.pt")
    results = model.train(
        data="data/user_data.yaml",
        epochs=50,
        imgsz=640
    )
    print("Training Completed!")

if __name__ == "__main__":
    train()
