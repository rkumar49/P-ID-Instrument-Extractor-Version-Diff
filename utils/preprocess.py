"""
Image preprocessing pipeline for OCR with Streamlit caching.
"""

import cv2
import numpy as np
import streamlit as st


def to_grayscale(image_np):
    """Convert RGB/RGBA image to single-channel grayscale."""
    if len(image_np.shape) == 2:
        return image_np
    if image_np.shape[2] == 4:
        return cv2.cvtColor(image_np, cv2.COLOR_RGBA2GRAY)
    return cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)


def denoise(gray, strength=3):
    """Remove small noise. strength=0 disables."""
    if strength <= 0:
        return gray
    h = strength if strength % 2 == 1 else strength + 1
    return cv2.fastNlMeansDenoising(
        gray, None, h=h, templateWindowSize=7, searchWindowSize=21
    )


def threshold(gray, block_size=31, c=15):
    """Adaptive thresholding for CAD with uneven lighting."""
    if block_size % 2 == 0:
        block_size += 1
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        c,
    )


def auto_invert(binary):
    """Invert if white-on-black (OCR prefers black-on-white)."""
    white_ratio = np.mean(binary == 255)
    if white_ratio < 0.5:
        return cv2.bitwise_not(binary)
    return binary


def upscale_if_small(binary, min_height=1500):
    """Upscale small images so OCR can read tiny dimension text."""
    h, w = binary.shape[:2]
    if h >= min_height:
        return binary
    scale = min_height / h
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(binary, new_size, interpolation=cv2.INTER_CUBIC)


@st.cache_data(show_spinner=False, max_entries=5)
def preprocess_pipeline(
    image_np,
    do_denoise=True,
    denoise_strength=3,
    do_threshold=True,
    block_size=31,
    c=15,
    do_invert=True,
    do_upscale=True,
):
    """Full preprocessing pipeline. Returns (processed_image, steps_dict)."""
    steps = {}

    gray = to_grayscale(image_np)
    steps["grayscale"] = gray

    if do_denoise:
        gray = denoise(gray, strength=denoise_strength)
    steps["denoised"] = gray

    if do_threshold:
        binary = threshold(gray, block_size=block_size, c=c)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    steps["binary"] = binary

    if do_invert:
        binary = auto_invert(binary)
    steps["final_binary"] = binary

    if do_upscale:
        binary = upscale_if_small(binary)
    steps["final"] = binary

    return binary, steps