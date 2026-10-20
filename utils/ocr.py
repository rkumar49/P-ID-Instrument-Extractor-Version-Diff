"""
OCR module — detects text in an image and returns structured results.

Functions:
    - get_reader():               Load & cache the EasyOCR reader
    - run_ocr():                  Run OCR -> list of detection dicts
    - draw_overlay():             Draw simple green boxes + labels
    - draw_categorized_overlay(): Draw category-colored boxes + labels

Uses EasyOCR. The reader is cached via st.cache_resource so the model
loads only once per Streamlit session.
"""

import os
import sys

import numpy as np
import streamlit as st
from PIL import Image
import cv2


# ============================================================
# READER (cached)
# ============================================================

@st.cache_resource(show_spinner=False)
def get_reader(langs=("en",), gpu=False):
    """Load & cache the EasyOCR reader."""
    import easyocr
    return easyocr.Reader(list(langs), gpu=gpu)


# ============================================================
# OCR
# ============================================================

def run_ocr(image, langs=("en",), gpu=False):
    """Run OCR on a PIL image or numpy array."""
    if isinstance(image, Image.Image):
        image_np = np.array(image.convert("RGB"))
    else:
        image_np = np.asarray(image)

    if image_np.dtype != np.uint8:
        image_np = image_np.astype(np.uint8)

    reader = get_reader(langs=langs, gpu=gpu)
    raw = reader.readtext(image_np, detail=1, paragraph=False)

    results = []
    for bbox, text, conf in raw:
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x1, x2 = int(min(xs)), int(max(xs))
        y1, y2 = int(min(ys)), int(max(ys))
        results.append({
            "text": text.strip(),
            "confidence": float(conf),
            "bbox": bbox,
            "x": x1,
            "y": y1,
            "w": x2 - x1,
            "h": y2 - y1,
        })
    return results


# ============================================================
# HELPERS
# ============================================================

def _as_rgb_np(image):
    """Convert PIL Image or numpy array to writable RGB numpy array."""
    if isinstance(image, Image.Image):
        arr = np.array(image.convert("RGB"))
    else:
        arr = np.asarray(image)
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    arr = np.array(arr, copy=True)
    return arr


# ============================================================
# SIMPLE OVERLAY (single color)
# ============================================================

def draw_overlay(image, detections, min_conf=0.0):
    """Draw green bounding boxes + white labels."""
    img_np = _as_rgb_np(image)

    for det in detections:
        if det["confidence"] < min_conf:
            continue

        x, y, w, h = det["x"], det["y"], det["w"], det["h"]
        cv2.rectangle(img_np, (x, y), (x + w, y + h), (0, 200, 0), 2)

        label = f"{det['text']} ({det['confidence']:.2f})"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        label_y_top = max(0, y - th - 6)

        cv2.rectangle(img_np, (x, label_y_top), (x + tw + 6, y), (0, 200, 0), -1)
        cv2.putText(
            img_np, label, (x + 3, max(12, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA,
        )

    return Image.fromarray(img_np)


# ============================================================
# CATEGORIZED OVERLAY (color per category)
# ============================================================

def draw_categorized_overlay(image, detections, min_conf=0.0):
    """Draw category-colored bounding boxes + labels."""
    try:
        from utils.classify import category_color
    except Exception:
        def category_color(_cat):
            return (0, 200, 0)

    img_np = _as_rgb_np(image)

    for det in detections:
        if det["confidence"] < min_conf:
            continue

        cat = det.get("category", "unknown")
        color = category_color(cat)

        x, y, w, h = det["x"], det["y"], det["w"], det["h"]
        cv2.rectangle(img_np, (x, y), (x + w, y + h), color, 2)

        label = f"{det['text']} [{cat[:3]}]"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        label_y_top = max(0, y - th - 5)

        cv2.rectangle(img_np, (x, label_y_top), (x + tw + 5, y), color, -1)
        cv2.putText(
            img_np, label, (x + 2, max(11, y - 4)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA,
        )

    return Image.fromarray(img_np)
