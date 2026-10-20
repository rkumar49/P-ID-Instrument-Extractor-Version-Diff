"""
CAD Dimension Detector - Main Streamlit App

Pipeline:
    1. Upload a CAD drawing (PDF or image)
    2. Preprocess (grayscale → threshold → clean)
    3. Compare original vs. preprocessed side by side
    4. Zoom Inspector with real scrollbars (0.1× to 10×)
    5. OCR detection (EasyOCR)
    6. Classification into categories
    7. Grouping into instrument records
    8. Human verification (checkbox per row)
    9. Export to CSV / Excel
"""

import io as _io
import os
import sys

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# ------------------------------------------------------------------
# Make project root importable
# ------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.preprocess import preprocess_pipeline
from utils.pdf_loader import pdf_to_image, pdf_page_count, pdf_has_text_layer
from utils.ui import side_by_side_comparison, zoom_inspector
from utils.ocr import run_ocr, draw_overlay, draw_categorized_overlay
from utils.classify import classify_text, group_instruments


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="CAD Dimension Detector",
    page_icon="📐",
    layout="wide",
)

st.title("📐 CAD Dimension Detector")
st.caption(
    "Upload a CAD drawing → preprocess → inspect → OCR → classify → verify → export."
)


# ============================================================
# SIDEBAR — PREPROCESSING
# ============================================================
st.sidebar.header("⚙️ Preprocessing")

do_denoise = st.sidebar.checkbox("Denoise", value=False)
denoise_strength = st.sidebar.slider(
    "Denoise strength", 0, 10, 3, disabled=not do_denoise,
)

do_threshold = st.sidebar.checkbox("Adaptive Threshold", value=True)
block_size = st.sidebar.slider(
    "Block size", 3, 71, 31, step=2, disabled=not do_threshold,
)
c_value = st.sidebar.slider(
    "C (constant subtracted)", -10, 30, 15, disabled=not do_threshold,
)

do_invert = st.sidebar.checkbox("Auto-invert if white-on-black", value=True)
do_upscale = st.sidebar.checkbox("Upscale small images", value=True)


# ============================================================
# SIDEBAR — OCR CONTROLS
# ============================================================
st.sidebar.header("🔎 OCR")

min_conf = st.sidebar.slider(
    "Minimum confidence",
    min_value=0.0,
    max_value=1.0,
    value=0.15,
    step=0.05,
    help="Lower to catch faint text. Engineering tags often score 0.15–0.4.",
)

use_gpu = st.sidebar.checkbox(
    "Use GPU (if available)",
    value=False,
    help="Leave off unless you have a CUDA-capable GPU.",
)


# ============================================================
# FILE UPLOADER
# ============================================================
uploaded_file = st.file_uploader(
    "Upload a CAD drawing",
    type=["pdf", "png", "jpg", "jpeg", "bmp", "tiff"],
)


# ============================================================
# MAIN
# ============================================================
if uploaded_file is None:
    st.info("👆 Please upload a CAD drawing to get started.")
    st.stop()

file_bytes = uploaded_file.read()
file_ext = uploaded_file.name.lower().rsplit(".", 1)[-1]

# ---------- Load ----------
image = None

if file_ext == "pdf":
    n_pages = pdf_page_count(file_bytes)

    st.sidebar.header("📄 PDF Options")
    st.sidebar.write(f"**Pages detected:** {n_pages}")

    page_num = st.sidebar.number_input(
        "Page to process (1-indexed)", 1, n_pages, 1, step=1,
    ) - 1

    dpi = st.sidebar.select_slider(
        "Render DPI", [100, 150, 200, 300, 400, 600], value=300,
    )

    with st.spinner(f"Rendering PDF page {page_num + 1} at {dpi} DPI..."):
        image = pdf_to_image(file_bytes, page_num=page_num, dpi=dpi)

    has_text, sample = pdf_has_text_layer(file_bytes, page_num)
    if has_text:
        st.success(f"✅ PDF has a text layer (sample: `{sample[:80]}...`)")
    else:
        st.info("ℹ️ No text layer — OCR is required.")

else:
    image = Image.open(uploaded_file).convert("RGB")

image_np = np.array(image)

# ---------- Preprocess ----------
with st.spinner("Preprocessing..."):
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

st.session_state["original_image"] = image_np
st.session_state["processed_image"] = processed
st.session_state["preprocess_steps"] = steps
st.session_state["filename"] = uploaded_file.name


# ============================================================
# SECTION 1 — SIDE-BY-SIDE COMPARISON
# ============================================================
st.subheader("1️⃣ Side-by-Side Comparison")
side_by_side_comparison(
    image_np, processed,
    label_left="Original",
    label_right="Preprocessed",
)
st.divider()


# ============================================================
# SECTION 2 — ZOOM INSPECTOR
# ============================================================
st.subheader("2️⃣ Zoom Inspector")
images_dict = {
    "Original (raw)": image_np,
    "Preprocessed (final)": processed,
    "1. Grayscale": steps.get("grayscale"),
    "2. Denoised": steps.get("denoised"),
    "3. Binary (thresholded)": steps.get("binary"),
    "4. Final binary": steps.get("final_binary"),
}
images_dict = {k: v for k, v in images_dict.items() if v is not None}
zoom_inspector(images_dict, key="main_inspector")
st.divider()


# ============================================================
# SECTION 3 — OCR + CLASSIFICATION + INSTRUMENT TABLE
# ============================================================
st.subheader("3️⃣ OCR Detection & Instrument Extraction")

st.caption(
    "EasyOCR reads text; results are classified into categories "
    "(instrument / tag / pipe size / note) and grouped into instrument records."
)

run_ocr_btn = st.button("🚀 Run OCR & Classify", type="primary")

if run_ocr_btn:
    with st.spinner("Running OCR... (first run downloads the model, 1–2 min)"):
        detections = run_ocr(processed, langs=("en",), gpu=use_gpu)

        # Classify every detection
        for d in detections:
            d["category"] = classify_text(d["text"])

        # Group into instrument records
        instruments = group_instruments(detections)

    st.session_state["detections"] = detections
    st.session_state["instruments"] = instruments
    st.success(
        f"✅ Detected **{len(detections)}** text regions · "
        f"Grouped into **{len(instruments)}** instrument records."
    )

# Retrieve from session
detections = st.session_state.get("detections", None)
instruments = st.session_state.get("instruments", None)

if detections is not None:
    filtered = [d for d in detections if d["confidence"] >= min_conf]
    st.write(f"**After confidence ≥ {min_conf:.2f}:** {len(filtered)} detections")

    # ---------------- Categorized overlay ----------------
    overlay_img = draw_categorized_overlay(processed, detections, min_conf=min_conf)

    st.markdown("##### 🎨 Categorized overlay (zoomable)")
    st.caption(
        "🟠 Instrument function · 🟣 System code · 🔵 Component ID · "
        "🟢 Pipe size · ⚪ Note/Noise"
    )

    zoom_inspector(
        {
            "Categorized overlay": overlay_img,
            "Preprocessed (no boxes)": processed,
            "Original (raw)": image_np,
        },
        key="overlay_inspector",
    )

    # ---------------- Category filter ----------------
    st.markdown("##### 🗂️ Filter by category")
    all_cats = sorted(set(d["category"] for d in filtered))
    selected_cats = st.multiselect(
        "Show only these categories:",
        options=all_cats,
        default=all_cats,
        key="cat_filter",
    )
    filtered_cat = [d for d in filtered if d["category"] in selected_cats]

    # ---------------- Detections table ----------------
    st.markdown("##### 📋 All detections")
    df_det = pd.DataFrame()
    if filtered_cat:
        df_det = pd.DataFrame([
            {
                "#": i + 1,
                "Raw OCR": d["text"],
                "Normalized": d.get("text_norm", d["text"]),
                ##"Text": d["text"],
                "Category": d["category"],
                "Confidence": round(d["confidence"], 3),
                "X": d["x"], "Y": d["y"], "W": d["w"], "H": d["h"],
            }
            for i, d in enumerate(filtered_cat)
        ])
        st.dataframe(df_det, use_container_width=True, height=300)
    else:
        st.info("No detections match the current filters.")

    # ---------------- Instrument schedule ----------------
    st.markdown("##### 🧾 Instrument schedule (grouped)")
    st.caption(
        "Each row is one instrument. Uncheck **✓** to exclude a row from export."
    )

    if instruments:
        df_inst = pd.DataFrame([
            {
                "Verify": True,
                "Function": r["func"],
                "System Code": r["system_code"] or "",
                "Component ID": r["component_id"] or "",
                "Pipe Sizes": ", ".join(r["pipe_sizes"]),
                "Confidence": round(r["confidence"], 3),
                "X": r["x"],
                "Y": r["y"],
            }
            for r in instruments
            if r["confidence"] >= min_conf
        ])

        if not df_inst.empty:
            edited = st.data_editor(
                df_inst,
                use_container_width=True,
                height=400,
                column_config={
                    "Verify": st.column_config.CheckboxColumn(
                        "✓",
                        help="Uncheck to exclude from export",
                        default=True,
                    ),
                },
                key="instrument_editor",
            )

            verified = edited[edited["Verify"] == True].drop(columns=["Verify"])
            st.caption(
                f"**{len(verified)} / {len(edited)}** rows verified — "
                f"only verified rows are exported."
            )

            # ---------------- Downloads ----------------
            col_dl1, col_dl2 = st.columns(2)

            with col_dl1:
                csv_bytes = verified.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "⬇️ Download verified instruments (CSV)",
                    data=csv_bytes,
                    file_name=f"instruments_{uploaded_file.name.rsplit('.', 1)[0]}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with col_dl2:
                excel_buf = _io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                    verified.to_excel(writer, sheet_name="Instruments", index=False)
                    if not df_det.empty:
                        df_det.to_excel(writer, sheet_name="All Detections", index=False)
                st.download_button(
                    "⬇️ Download Excel (2 sheets)",
                    data=excel_buf.getvalue(),
                    file_name=f"report_{uploaded_file.name.rsplit('.', 1)[0]}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
        else:
            st.info("No instruments above the confidence threshold.")
    else:
        st.info("No instruments detected above the confidence threshold.")

else:
    st.info("Click **🚀 Run OCR & Classify** to analyze the preprocessed image.")

st.divider()


# ============================================================
# SECTION 4 — EXPORT IMAGES
# ============================================================
st.subheader("4️⃣ Export Images")

col_img1, col_img2 = st.columns(2)

with col_img1:
    st.download_button(
        "⬇️ Download preprocessed image",
        data=Image.fromarray(processed).tobytes(),
        file_name=f"preprocessed_{uploaded_file.name.rsplit('.', 1)[0]}.png",
        mime="image/png",
        use_container_width=True,
    )

with col_img2:
    if detections is not None:
        st.download_button(
            "⬇️ Download categorized overlay",
            data=overlay_img.tobytes(),
            file_name=f"overlay_{uploaded_file.name.rsplit('.', 1)[0]}.png",
            mime="image/png",
            use_container_width=True,
        )


# ============================================================
# SIDEBAR — INFO
# ============================================================
st.sidebar.header("📊 Info")
st.sidebar.write(f"**File:** {uploaded_file.name}")
st.sidebar.write(f"**Original size:** {image.size}")
st.sidebar.write(f"**Processed shape:** {processed.shape}")
if detections is not None:
    st.sidebar.write(f"**Detections:** {len(detections)}")
if instruments is not None:
    st.sidebar.write(f"**Instruments:** {len(instruments)}")