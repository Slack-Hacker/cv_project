from fastapi import APIRouter
import os

router = APIRouter()

TRAIN_LABELS = "data/train_tmp/labels"
MANUAL_LABELS = "data/user_object/labels"

@router.get("/labels/status")
def label_status():
    """Return dictionary marking which images already have labels."""
    result = {}

    # All label files in both folders
    train_lbls = {f.rsplit(".", 1)[0] for f in os.listdir(TRAIN_LABELS) if f.endswith(".txt")}
    manual_lbls = {f.rsplit(".", 1)[0] for f in os.listdir(MANUAL_LABELS) if f.endswith(".txt")}

    combined = train_lbls | manual_lbls

    for name in combined:
        result[name] = True  # label exists

    return result
