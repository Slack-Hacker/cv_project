import os

def clear_cache(folder="data/cache/"):
    if not os.path.exists(folder):
        return
    for f in os.listdir(folder):
        os.remove(os.path.join(folder, f))
