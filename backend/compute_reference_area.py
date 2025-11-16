import os
import json

LABEL_DIR = "data/user_object/labels/"
OUT_PATH = "data/user_object/reference_area.json"

areas = []

for fname in os.listdir(LABEL_DIR):
    if fname.endswith(".txt"):
        path = os.path.join(LABEL_DIR, fname)

        # read label
        with open(path, "r") as f:
            parts = f.readline().strip().split()
        
        # YOLO format: class xc yc w h
        w = float(parts[3])
        h = float(parts[4])

        # bbox area in normalized scale (0 to 1)
        area_norm = w * h
        areas.append(area_norm)

if len(areas) == 0:
    print("No labels found!")
    exit()

# Compute median area
areas_sorted = sorted(areas)
mid = len(areas_sorted) // 2
if len(areas_sorted) % 2 == 0:
    median_area = (areas_sorted[mid-1] + areas_sorted[mid]) / 2
else:
    median_area = areas_sorted[mid]

with open(OUT_PATH, "w") as f:
    json.dump({"reference_area_norm": median_area}, f, indent=2)

print("Reference area saved:", median_area)
