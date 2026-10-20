import cv2
import numpy as np
from PIL import Image

def load_with_pillow(path):
    """Load with Pillow (RGB)."""
    img = Image.open(path)
    arr = np.array(img)
    print(f"Pillow → mode={img.mode}, size={img.size}, shape={arr.shape}")
    return img, arr

def load_with_opencv(path):
    """Load with OpenCV (BGR by default)."""
    img = cv2.imread(path)              # BGR
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    print(f"OpenCV → shape={img.shape}, dtype={img.dtype}")
    return img, img_rgb

if __name__ == "__main__":
    path = "data/im-a-design-engineer-roast-my-print-v0-vz3vhjlnuaif1.png"
    load_with_pillow(path)
    load_with_opencv(path)