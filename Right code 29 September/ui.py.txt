"""
UI helpers for the CAD Dimension Detector.

Provides:
    - _to_pil():               Convert numpy/PIL → RGB PIL Image
    - side_by_side_comparison: Two images side by side with a divider
    - zoom_inspector:          Zoom with REAL scrollbars (HTML/JS viewer)
"""

import streamlit as st
import numpy as np
from PIL import Image
import base64
import io
import streamlit.components.v1 as components


# ============================================================
# HELPERS
# ============================================================

def _to_pil(img):
    """Convert numpy array or PIL Image to RGB PIL Image."""
    if isinstance(img, np.ndarray):
        if img.ndim == 2:
            img = np.stack([img] * 3, axis=-1)
        return Image.fromarray(img.astype(np.uint8)).convert("RGB")
    return img.convert("RGB")


def _pil_to_base64_png(pil):
    """Encode a PIL image to a base64 PNG string for embedding in HTML."""
    buf = io.BytesIO()
    pil.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ============================================================
# SIDE-BY-SIDE COMPARISON
# ============================================================

def side_by_side_comparison(
    img_left,
    img_right,
    label_left="Original",
    label_right="Preprocessed",
):
    """Simple side-by-side comparison using st.image."""
    col1, divider, col2 = st.columns([10, 1, 10])

    with col1:
        st.markdown(
            f"""<h3 style="text-align:center; color:#1f77b4; margin-bottom:6px;">
                📄 {label_left}
            </h3>""",
            unsafe_allow_html=True,
        )
        st.image(_to_pil(img_left), use_container_width=True)

    with divider:
        st.markdown(
            """<div style="
                border-left: 3px dashed #999999;
                height: 100%;
                min-height: 500px;
                margin-top: 50px;
            "></div>""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""<h3 style="text-align:center; color:#d62728; margin-bottom:6px;">
                ⚙️ {label_right}
            </h3>""",
            unsafe_allow_html=True,
        )
        st.image(_to_pil(img_right), use_container_width=True)


# ============================================================
# ZOOM INSPECTOR — REAL SCROLLBARS via HTML/JS
# ============================================================

def zoom_inspector(images_dict, key="zoom_inspector"):
    """
    Full-resolution zoom viewer with REAL browser scrollbars.

    Image is scaled by a zoom factor (CSS width = full_w * zoom),
    placed inside a scrollable div. Browser shows native scrollbars.
    """
    if not images_dict:
        st.warning("No images to inspect.")
        return None

    labels = list(images_dict.keys())

    # -------- Selector --------
    selected = st.selectbox(
        "Choose image to inspect",
        options=labels,
        key=f"{key}_select",
        help="Pick which version to inspect at full resolution.",
    )

    pil = _to_pil(images_dict[selected])

    # -------- Controls row --------
    c1, c2, c3 = st.columns([2, 2, 4])

    with c1:
        zoom = st.slider(
            "Zoom",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.25,
            key=f"{key}_zoom",
        )

    with c2:
        viewer_height = st.slider(
            "Viewer height (px)",
            min_value=400,
            max_value=1200,
            value=700,
            step=50,
            key=f"{key}_vheight",
        )

    with c3:
        st.caption(
            "🖱️ Scroll inside the box (wheel, or drag the scrollbars). "
            "The image is not resampled — you always see original pixels."
        )

    # -------- Build HTML viewer --------
    img_b64 = _pil_to_base64_png(pil)
    full_w, full_h = pil.size
    display_w = int(full_w * zoom)
    display_h = int(full_h * zoom)

    # Pre-format the JS-safe zoom string OUTSIDE the f-string
    # to avoid the `{x}` / `{y}` interpretation problem entirely.
    zoom_str = f"{zoom:.2f}"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: transparent;
        }
        .viewer-wrap {
            position: relative;
            border: 1px solid #cccccc;
            border-radius: 4px;
            background: #f7f7f7;
            padding: 0;
            overflow: hidden;
        }
        .viewer {
            width: 100%;
            height: __VIEWER_HEIGHT__px;
            overflow: auto;
            background: #ffffff;
            position: relative;
        }
        .viewer img {
            display: block;
            width: __DISPLAY_W__px;
            height: __DISPLAY_H__px;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
            user-select: none;
            -webkit-user-drag: none;
        }
        .hint {
            position: absolute;
            top: 8px;
            right: 12px;
            background: rgba(0,0,0,0.55);
            color: white;
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 10px;
            pointer-events: none;
        }
    </style>
    </head>
    <body>
        <div class="viewer-wrap">
            <div class="viewer" id="viewer">
                <img src="data:image/png;base64,__IMG_B64__" alt="CAD drawing">
            </div>
            <div class="hint" id="hint">Zoom __ZOOM_STR__×</div>
        </div>

        <script>
            const viewer = document.getElementById('viewer');
            const hint = document.getElementById('hint');
            const baseZoom = "__ZOOM_STR__";

            function updateHint() {
                const x = Math.round(viewer.scrollLeft);
                const y = Math.round(viewer.scrollTop);
                hint.textContent = 'Zoom ' + baseZoom + '× · scroll (' + x + ', ' + y + ')';
            }

            viewer.addEventListener('scroll', updateHint);
            updateHint();
        </script>
    </body>
    </html>
    """

    # Now safely substitute placeholders (no f-string brace conflicts)
    html = (
        html
        .replace("__VIEWER_HEIGHT__", str(viewer_height))
        .replace("__DISPLAY_W__", str(display_w))
        .replace("__DISPLAY_H__", str(display_h))
        .replace("__IMG_B64__", img_b64)
        .replace("__ZOOM_STR__", zoom_str)
    )

    components.html(html, height=viewer_height + 30, scrolling=False)

    # -------- Info line --------
    st.caption(
        f"Original: **{full_w} × {full_h}** px · "
        f"Displayed at **{display_w} × {display_h}** px "
        f"(Zoom {zoom:.2f}×) · "
        f"Scrollbars appear when the image exceeds the viewer."
    )

    return {
        "zoom": zoom,
        "display_size": (display_w, display_h),
        "original_size": (full_w, full_h),
    }