"""
CAD Dimension Detector - Main Streamlit App

Stages 1-3.6: Upload (PDF/image) → Preprocess → Display with zoom.
"""

import streamlit as st
import numpy as np
from PIL import Image
import sys
import os

# Make utils importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.preprocess import preprocess_pipeline
from utils.pdf_loader import pdf_to_image, pdf_page_count, pdf_has_text_layer
from utils.ui import zoomable_image, side_by_side_zoomable


# ============================================================
# PAGE CONFIG (must be first Streamlit call)
# ============================================================
st.set_page_config(
    page_title="CAD Dimension Detector",
    page_icon="📐",
    layout="wide",
)

st.title("📐 CAD Dimension Detector")
st.caption("Upload a CAD drawing (PDF or image) to detect and extract dimensions.")


# ============================================================
# SIDEBAR: PREPROCESSING CONTROLS
# ============================================================
st.sidebar.header("⚙️ Preprocessing")

do_denoise = st.sidebar.checkbox("Denoise", value=True)
denoise_strength = st.sidebar.slider(
    "Denoise strength", 0, 10, 3,
    disabled=not do_denoise,
    help="Higher = more aggressive noise removal",
)

do_threshold = st.sidebar.checkbox("Adaptive Threshold", value=True)
block_size = st.sidebar.slider(
    "Block size", 3, 71, 31, step=2,
    disabled=not do_threshold,
    help="Neighborhood size for thresholding. Must be odd.",
)
c_value = st.sidebar.slider(
    "C (constant subtracted)", -10, 30, 15,
    disabled=not do_threshold,
    help="Higher = more aggressive binarization (thinner text)",
)

do_invert = st.sidebar.checkbox("Auto-invert if white-on-black", value=True)
do_upscale = st.sidebar.checkbox("Upscale small images", value=True)


# ============================================================
# SIDEBAR: DISPLAY CONTROLS
# ============================================================
st.sidebar.header("🔍 Display")

display_size = st.sidebar.slider(
    "Display width (px)", 400, 1200, 700, step=50,
    help="Lower = faster page. You can still zoom inside the viewer.",
)

zoom_mode = st.sidebar.selectbox(
    "Zoom interaction mode",
    options=["dragmove", "scroll", "both", "mousemove"],
    index=0,
    help=(
        "dragmove: click to zoom, drag to pan, double-click to reset · "
        "scroll: wheel zoom only · "
        "both: scroll + mousemove · "
        "mousemove: zoom follows mouse"
    ),
)

keep_resolution = st.sidebar.checkbox(
    "High-res zoom (slower)",
    value=False,
    help="When ON, zoom uses the full-resolution image. Sharper but slower on huge CAD sheets.",
)


# ============================================================
# FILE UPLOAD
# ============================================================
uploaded_file = st.file_uploader(
    "Upload a CAD drawing",
    type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff"],
)


# ============================================================
# MAIN LOGIC
# ============================================================
if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    file_ext = uploaded_file.name.lower().rsplit(".", 1)[-1]

    image = None  # Will hold the PIL Image

    # ---------- PDF branch ----------
    if file_ext == "pdf":
        n_pages = pdf_page_count(file_bytes)

        st.sidebar.header("📄 PDF Options")
        st.sidebar.write(f"**Pages detected:** {n_pages}")

        page_num = st.sidebar.number_input(
            "Page to process (1-indexed)",
            min_value=1,
            max_value=n_pages,
            value=1,
            step=1,
        ) - 1  # Convert to 0-indexed

        dpi = st.sidebar.select_slider(
            "Render DPI",
            options=[100, 150, 200, 300, 400, 600],
            value=300,
            help="Higher = sharper but slower. 300 is the CAD standard.",
        )

        with st.spinner(f"Rendering PDF page {page_num + 1} at {dpi} DPI..."):
            image = pdf_to_image(file_bytes, page_num=page_num, dpi=dpi)

        # Check for text layer
        has_text, sample = pdf_has_text_layer(file_bytes, page_num)
        if has_text:
            st.success(f"✅ PDF has a text layer (sample: `{sample[:80]}...`)")
        else:
            st.info("ℹ️ No text layer found — this CAD PDF exported text as outlines. **OCR is required.**")

    # ---------- Image branch ----------
    else:
        image = Image.open(uploaded_file).convert("RGB")

    # ---------- Convert to numpy and preprocess ----------
    image_np = np.array(image)

    processed, steps = preprocess_pipeline(
        image_np,
        do_denoise=do_denoise,
        denoise_strength=denoise_strength,
        do_threshold=do_threshold,
        block_size=block_size,
        c=c_value,
        do_invert=do_invert,
        do_upscale=do_upscale,
    )

    # ---------- Side-by-side zoomable preview ----------
    st.subheader("Original vs. Preprocessed")
    st.caption(
        "**Interaction:** Single-click to zoom in · Drag to pan · Double-click to reset. "
        "Each image zooms independently."
    )

    side_by_side_zoomable(
        image_np,
        processed,
        label_left="Original",
        label_right="Preprocessed (what OCR sees)",
        key_prefix="main",
        display_size=display_size,
        mode=zoom_mode,
    )

    # ---------- Intermediate steps (all zoomable) ----------
    with st.expander("🔍 View intermediate preprocessing steps"):
        for name in ["grayscale", "denoised", "binary", "final_binary", "final"]:
            if name in steps:
                st.write(f"**{name}** — shape `{steps[name].shape}`")
                zoomable_image(
                    steps[name],
                    key=f"step_{name}",
                    display_size=display_size,
                    mode=zoom_mode,
                )

    # ---------- Store in session state for future stages ----------
    st.session_state["processed_image"] = processed
    st.session_state["original_image"] = image_np
    st.session_state["filename"] = uploaded_file.name

    # ---------- Download preprocessed ----------
    st.download_button(
        "⬇️ Download preprocessed image",
        data=Image.fromarray(processed).tobytes(),
        file_name=f"preprocessed_{uploaded_file.name.rsplit('.', 1)[0]}.png",
        mime="image/png",
    )

    # ---------- Sidebar info ----------
    st.sidebar.header("📊 Image Info")
    st.sidebar.write(f"**Filename:** {uploaded_file.name}")
    st.sidebar.write(f"**Original size:** {image.size}")
    st.sidebar.write(f"**Processed shape:** {processed.shape}")

else:
    st.info("👆 Please upload a CAD drawing to get started.")
    st.stop()