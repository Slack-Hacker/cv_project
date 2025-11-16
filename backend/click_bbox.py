import cv2
import json
import sys
from pathlib import Path
import os

# ----------- CHECK ARGUMENTS --------------
if len(sys.argv) < 2:
    print("Usage: python click_bbox.py data/user_object/images/<image>.jpg")
    sys.exit(1)

image_path = sys.argv[1]
img = cv2.imread(image_path)

if img is None:
    print("❌ ERROR: Cannot load image:", image_path)
    sys.exit(1)

coords = []
clone = img.copy()

print("\n====================================")
print("2-CLICK BOUNDING BOX TOOL (OpenCV)")
print("====================================")
print("Instructions:")
print("1️⃣ Left-click TOP-LEFT of object")
print("2️⃣ Left-click BOTTOM-RIGHT of object")
print("Press 'r' to reset clicks")
print("Press 'q' to finish and save coords\n")

def click_event(event, x, y, flags, param):
    global coords, clone
    if event == cv2.EVENT_LBUTTONDOWN:
        coords.append((x, y))
        cv2.circle(clone, (x, y), 5, (0,255,0), -1)
        cv2.putText(clone, f"{len(coords)}", (x+5, y-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.imshow("Image", clone)

# Setup window
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.imshow("Image", clone)
cv2.setMouseCallback("Image", click_event)

# UI Loop
while True:
    key = cv2.waitKey(1) & 0xFF

    if key == ord('r'):
        clone = img.copy()
        coords = []
        cv2.imshow("Image", clone)
        print("🔄 Reset clicks.")

    elif key == ord('q'):
        break

cv2.destroyAllWindows()

# After closing window:
if len(coords) < 2:
    print("❌ You did not click twice.")
    sys.exit(1)

# Extract x1,y1,x2,y2
(x1, y1) = coords[0]
(x2, y2) = coords[1]

# Normalize order (ensure correct order)
x1n, x2n = min(x1, x2), max(x1, x2)
y1n, y2n = min(y1, y2), max(y1, y2)

h, w = img.shape[:2]

# Output
result = {
    "image": Path(image_path).name,
    "x1": int(x1n),
    "y1": int(y1n),
    "x2": int(x2n),
    "y2": int(y2n),
    "img_w": int(w),
    "img_h": int(h)
}

print("\n📌 FINAL COORDINATES")
print(json.dumps(result, indent=4))

# ----------- SAVE JSON IN user_object FOLDER -------------
USER_OBJECT_DIR = Path("data/user_object/")
USER_OBJECT_DIR.mkdir(parents=True, exist_ok=True)

json_name = Path(image_path).name.replace(Path(image_path).suffix, ".coords.json")
out_path = USER_OBJECT_DIR / json_name

with open(out_path, "w") as f:
    json.dump(result, f, indent=4)

print(f"\n💾 Saved to: {out_path}\n")
print("Use these values in POSTMAN for `/api/label/manual`")
