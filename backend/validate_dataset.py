import os

IMG_DIR = "data/user_object/images/"
LABEL_DIR = "data/user_object/labels/"

images = {f.split('.')[0] for f in os.listdir(IMG_DIR)}
labels = {f.split('.')[0] for f in os.listdir(LABEL_DIR)}

missing = images - labels
extra = labels - images

if missing:
    print("Missing labels for:", missing)
if extra:
    print("Labels without images:", extra)

if not missing and not extra:
    print("Dataset looks good!")
