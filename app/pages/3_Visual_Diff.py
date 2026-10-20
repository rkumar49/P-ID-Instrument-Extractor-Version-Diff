"""
Visual Diff — side-by-side annotated view of two versions.
"""

import io
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.oracle import (
    load_documents,
    load_instruments,
    load_detections,
    get_render_path,
)
from utils.diff import compare_versions
from utils.ui import zoom_inspector


st.set_page_config(page_title="Visual Diff", page_icon="🔍", layout="wide")
st.title("🔍 Visual Diff")
st.caption("Side-by-side view of two CAD versions with change highlights.")

COLORS = {
    "added":          (34, 197, 94),
    "deleted":        (239, 68, 68),
    "modified":       (234, 179, 8),
    "modified+moved": (249, 115, 22),
    "moved":          (59, 130, 246),
    "moved-far":      (59, 130, 246),
    "unchanged":      (200, 200, 200),
}


# ============================================================
# HELPERS
# ============================================================
def _load_png(path):
    if not path or not Path(path).exists():
        return None
    return Image.open(path).convert("RGB")


def _coerce_int(v):
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _normalize(t):
    """Strip '=', uppercase, strip trailing L/H from component IDs."""
    if t is None:
        return ""
    s = str(t).strip().upper()
    if s.startswith("="):
        s = s[1:].strip()
    s = re.sub(r"^([A-Z]{2,4}\d{2,4}\-[A-Z]{2,4}\d+)[LH]$", r"\1", s)
    return s


def _dist(r1, r2):
    x1, y1 = int(r1.get("X", 0) or 0), int(r1.get("Y", 0) or 0)
    x2, y2 = int(r2.get("X", 0) or 0), int(r2.get("Y", 0) or 0)
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


# ============================================================
# DRAW BOXES
# ============================================================
def _draw_boxes(img, rows, statuses_to_show, label_prefix=""):
    img = img.copy()
    draw = ImageDraw.Draw(img)
    img_w, img_h = img.size

    all_x, all_y = [], []
    for _, row in rows.iterrows():
        for col in ("X (old)", "X (new)"):
            v = _coerce_int(row.get(col))
            if v is not None:
                all_x.append(v)
        for col in ("Y (old)", "Y (new)"):
            v = _coerce_int(row.get(col))
            if v is not None:
                all_y.append(v)

    max_x_data = max(all_x) if all_x else img_w
    max_y_data = max(all_y) if all_y else img_h
    scale_x = img_w / max_x_data if max_x_data > img_w else 1.0
    scale_y = img_h / max_y_data if max_y_data > img_h else 1.0

    print(f"[VISDIFF{label_prefix}] image={img.size} "
          f"maxX={max_x_data} maxY={max_y_data} "
          f"scale=({scale_x:.3f},{scale_y:.3f})")

    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    drawn = 0
    for _, row in rows.iterrows():
        status = row["Status"]
        if status not in statuses_to_show:
            continue

        if status in ("added", "modified", "modified+moved", "moved", "moved-far"):
            x_raw, y_raw = row.get("X (new)"), row.get("Y (new)")
            w_raw, h_raw = row.get("W (new)"), row.get("H (new)")
        else:
            x_raw, y_raw = row.get("X (old)"), row.get("Y (old)")
            w_raw, h_raw = row.get("W (old)"), row.get("H (old)")

        x = _coerce_int(x_raw)
        y = _coerce_int(y_raw)
        if x is None or y is None:
            continue

        x = int(x * scale_x)
        y = int(y * scale_y)

        w_val = _coerce_int(w_raw) or 100
        h_val = _coerce_int(h_raw) or 30
        if w_val < 10:
            w_val = 100
        if h_val < 10:
            h_val = 30

        cx = x + int(w_val * scale_x) // 2
        cy = y + int(h_val * scale_y) // 2
        pad = 20
        half_w = min(int(w_val * scale_x) // 2 + pad, 400)
        half_h = min(int(h_val * scale_y) // 2 + pad, 200)

        x1 = max(0, cx - half_w)
        y1 = max(0, cy - half_h)
        x2 = min(img_w, cx + half_w)
        y2 = min(img_h, cy + half_h)

        color = COLORS.get(status, (0, 0, 0))
        draw.rectangle([x1, y1, x2, y2], outline=color, width=5)

        comp = str(row.get("Component ID", "") or "")
        if len(comp) > 30:
            comp = comp[:27] + "..."
        label_text = f"{status[0].upper()}: {comp}"

        try:
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except Exception:
            text_w, text_h = 100, 18

        lx1 = x1
        ly1 = max(0, y1 - text_h - 8)
        lx2 = min(img_w, x1 + text_w + 12)
        ly2 = y1

        draw.rectangle([lx1, ly1, lx2, ly2], fill=color)
        draw.text((lx1 + 6, ly1 + 2), label_text, fill=(255, 255, 255), font=font)
        drawn += 1

    print(f"[VISDIFF{label_prefix}] drew {drawn} boxes")
    return img, drawn


def _resize_for_export(img, max_side=4000):
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    scale = max_side / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)


def _png_bytes(img):
    buf = io.BytesIO()
    resized = _resize_for_export(img)
    resized.save(buf, format="PNG", optimize=True)
    return buf.getvalue(), resized.size


# ============================================================
# LOAD DOCUMENTS
# ============================================================
try:
    docs = load_documents()
except Exception as e:
    st.error(f"Oracle error: {e}")
    st.stop()

if docs.empty or len(docs) < 2:
    st.warning("Need at least 2 saved versions to compare.")
    st.stop()


def label(row):
    return f"#{row['DOC_ID']} — {row['FILENAME']} ({row['VERSION_LABEL']})"


c1, c2 = st.columns(2)
with c1:
    old_id = st.selectbox(
        "🕐 Old version",
        options=docs["DOC_ID"].tolist(),
        format_func=lambda x: label(docs[docs["DOC_ID"] == x].iloc[0]),
        index=len(docs) - 1,
        key="vis_old_id",
    )
with c2:
    new_id = st.selectbox(
        "🆕 New version",
        options=docs["DOC_ID"].tolist(),
        format_func=lambda x: label(docs[docs["DOC_ID"] == x].iloc[0]),
        index=0,
        key="vis_new_id",
    )

if old_id == new_id:
    st.warning("Pick two different versions.")
    st.stop()


# ============================================================
# LOAD INSTRUMENTS + DETECTIONS
# ============================================================
df_old = load_instruments(old_id)
df_new = load_instruments(new_id)

if df_old.empty or df_new.empty:
    st.warning("One of the versions has no instrument data.")
    st.stop()

diff = compare_versions(df_old, df_new, move_threshold_px=50)
print(f"[VISDIFF] instrument diff: {len(diff)} rows")

try:
    dets_old = load_detections(old_id)
    dets_new = load_detections(new_id)
except Exception as e:
    print(f"[VISDIFF] detections load failed: {e}")
    dets_old = pd.DataFrame()
    dets_new = pd.DataFrame()


# ============================================================
# BUILD TEXT DIFF
# ============================================================
def _text_key_exact(row):
    return (
        _normalize(row.get("TEXT_RAW")),
        int(row.get("X", 0) or 0) // 500,
        int(row.get("Y", 0) or 0) // 500,
    )


text_diff_rows = []

if not dets_old.empty and not dets_new.empty:
    old_list = [dict(r) for _, r in dets_old.iterrows()]
    new_list = [dict(r) for _, r in dets_new.iterrows()]
    matched_new_idx = set()

    # Pass 1: exact bucket
    for o in old_list:
        k = _text_key_exact(o)
        for j, n in enumerate(new_list):
            if j in matched_new_idx:
                continue
            if _text_key_exact(n) == k:
                matched_new_idx.add(j)
                o["_matched_new_idx"] = j
                break

    # Pass 2: text + nearest position
    for o in old_list:
        if "_matched_new_idx" in o:
            continue
        text_o = _normalize(o.get("TEXT_RAW"))
        if not text_o:
            continue
        best_j, best_d = None, float("inf")
        for j, n in enumerate(new_list):
            if j in matched_new_idx:
                continue
            if _normalize(n.get("TEXT_RAW")) != text_o:
                continue
            d = _dist(o, n)
            if d < best_d:
                best_d = d
                best_j = j
        if best_j is not None:
            matched_new_idx.add(best_j)
            o["_matched_new_idx"] = best_j

    # Build rows for matched old -> new
    for o in old_list:
        o_x, o_y = int(o["X"]), int(o["Y"])
        text = _normalize(str(o.get("TEXT_RAW", "")))
        cat = str(o.get("CATEGORY", "unknown"))
        if cat in ("note", "noise"):
            continue

        if "_matched_new_idx" in o:
            n = new_list[o["_matched_new_idx"]]
            n_x, n_y = int(n["X"]), int(n["Y"])
            dx, dy = n_x - o_x, n_y - o_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 50:
                continue
            status = "moved-far" if dist >= 300 else "moved"
        else:
            n = None
            n_x, n_y = "", ""
            dx, dy, dist = "", "", ""
            status = "deleted"

        text_diff_rows.append({
            "Status": status,
            "Component ID": text,
            "Func (old)": "", "Func (new)": "",
            "Sys (old)": "", "Sys (new)": "",
            "Pipe (old)": "", "Pipe (new)": "",
            "X (old)": o_x, "Y (old)": o_y,
            "X (new)": n_x, "Y (new)": n_y,
            "ΔX": dx, "ΔY": dy,
            "Δ Dist": round(dist, 1) if isinstance(dist, float) else "",
            "W (old)": int(o.get("W", 0) or 0),
            "H (old)": int(o.get("H", 0) or 0),
            "W (new)": int(n.get("W", 0) or 0) if n is not None else "",
            "H (new)": int(n.get("H", 0) or 0) if n is not None else "",
            "Source": "text",
            "Category": cat,
        })

    # Remaining new = added
    for j, n in enumerate(new_list):
        if j in matched_new_idx:
            continue
        cat = str(n.get("CATEGORY", "unknown"))
        if cat in ("note", "noise"):
            continue
        text_diff_rows.append({
            "Status": "added",
            "Component ID": _normalize(str(n.get("TEXT_RAW", ""))),
            "Func (old)": "", "Func (new)": "",
            "Sys (old)": "", "Sys (new)": "",
            "Pipe (old)": "", "Pipe (new)": "",
            "X (old)": "", "Y (old)": "",
            "X (new)": int(n["X"]), "Y (new)": int(n["Y"]),
            "ΔX": "", "ΔY": "", "Δ Dist": "",
            "W (old)": "", "H (old)": "",
            "W (new)": int(n.get("W", 0) or 0),
            "H (new)": int(n.get("H", 0) or 0),
            "Source": "text",
            "Category": cat,
        })

text_diff = pd.DataFrame(text_diff_rows) if text_diff_rows else pd.DataFrame()

if not text_diff.empty:
    comp_ids_in_diff = set()
    for cid in diff["Component ID"].dropna().astype(str):
        comp_ids_in_diff.add(cid.strip().upper())
    text_diff = text_diff[
        ~text_diff["Component ID"].astype(str).str.upper().isin(comp_ids_in_diff)
    ]
    print(f"[VISDIFF] text diff rows: {len(text_diff)}")


# ============================================================
# MERGE
# ============================================================
def _merge_diff(instr, text):
    instr = instr.copy()
    text = text.copy() if not text.empty else pd.DataFrame()

    all_cols = list(set(instr.columns) | set(text.columns))
    for c in all_cols:
        if c not in instr.columns:
            instr[c] = ""
        if not text.empty and c not in text.columns:
            text[c] = ""

    for c in all_cols:
        instr[c] = instr[c].apply(lambda v: "" if pd.isna(v) else str(v))
        if not text.empty:
            text[c] = text[c].apply(lambda v: "" if pd.isna(v) else str(v))

    instr = instr[all_cols]
    if not text.empty:
        text = text[all_cols]

    return instr if text.empty else pd.concat([instr, text], ignore_index=True)


merged = _merge_diff(diff, text_diff)
merged = merged.reset_index(drop=True)
print(f"[VISDIFF] merged diff shape: {merged.shape}")


# ============================================================
# FILTERS
# ============================================================
st.markdown("### 🎛️ Filters")
statuses = st.multiselect(
    "Show statuses:",
    ["added", "deleted", "modified", "modified+moved", "moved", "moved-far", "unchanged"],
    default=["added", "deleted", "modified", "modified+moved", "moved", "moved-far"],
    key="vis_statuses",
)

counts = merged["Status"].value_counts().to_dict()
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("➕ Added", counts.get("added", 0))
m2.metric("❌ Deleted", counts.get("deleted", 0))
m3.metric("🔄 Modified", counts.get("modified", 0) + counts.get("modified+moved", 0))
m4.metric("↔️ Moved", counts.get("moved", 0) + counts.get("moved-far", 0))
m5.metric("✅ Unchanged", counts.get("unchanged", 0))


# ============================================================
# LOAD IMAGES
# ============================================================
old_png = get_render_path(old_id)
new_png = get_render_path(new_id)

img_old = _load_png(old_png)
img_new = _load_png(new_png)

if img_old is None or img_new is None:
    st.error(
        "⚠️ Rendered images not found for one of the versions.\n\n"
        "Go to the main page and re-save both documents so PNG renders exist."
    )
    st.stop()


# ============================================================
# DRAW + DISPLAY
# ============================================================
old_annotated, old_count = _draw_boxes(img_old, merged, statuses, label_prefix=" old")
new_annotated, new_count = _draw_boxes(img_new, merged, statuses, label_prefix=" new")

st.markdown("### 🖼️ Side-by-Side Comparison")
st.caption(f"Old: **{old_count}** boxes · New: **{new_count}** boxes.")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown(
        f"<h4 style='text-align:center; color:#1f77b4;'>🕐 Old #{old_id}</h4>",
        unsafe_allow_html=True,
    )
    zoom_inspector(
        {"Annotated (old)": old_annotated, "Original (old)": img_old},
        key="vis_old_inspector",
    )

with col_b:
    st.markdown(
        f"<h4 style='text-align:center; color:#d62728;'>🆕 New #{new_id}</h4>",
        unsafe_allow_html=True,
    )
    zoom_inspector(
        {"Annotated (new)": new_annotated, "Original (new)": img_new},
        key="vis_new_inspector",
    )


# ============================================================
# LEGEND
# ============================================================
st.markdown("### 📖 Legend")
lc = st.columns(6)
lc[0].markdown("🟩 **Added**")
lc[1].markdown("🟥 **Deleted**")
lc[2].markdown("🟨 **Modified**")
lc[3].markdown("🟧 **Mod+Moved**")
lc[4].markdown("🟦 **Moved**")
lc[5].markdown("⬜ Unchanged")


# ============================================================
# DETAILS TABLE
# ============================================================
st.markdown("### 📋 Changed Instruments")
changed = merged[merged["Status"].isin(statuses)]

if changed.empty:
    st.success("No changes to display.")
else:
    display_cols = [
        "Status", "Component ID", "Category", "Source",
        "Func (old)", "Func (new)",
        "Sys (old)", "Sys (new)",
        "Pipe (old)", "Pipe (new)",
        "X (old)", "Y (old)", "X (new)", "Y (new)",
        "ΔX", "ΔY", "Δ Dist",
    ]
    display_cols = [c for c in display_cols if c in changed.columns]
    st.dataframe(changed[display_cols], width="stretch", height=400)


# ============================================================
# EXPORT
# ============================================================
st.markdown("### 📥 Export")
st.caption("Exports reflect the current **status filter**.")

old_bytes, old_size = None, None
new_bytes, new_size = None, None

try:
    old_bytes, old_size = _png_bytes(old_annotated)
    print(f"[VISDIFF export] OLD PNG: {len(old_bytes)/1024:.1f} KB size={old_size}")
except Exception as e:
    st.error(f"❌ Failed to prepare OLD image: {e}")

try:
    new_bytes, new_size = _png_bytes(new_annotated)
    print(f"[VISDIFF export] NEW PNG: {len(new_bytes)/1024:.1f} KB size={new_size}")
except Exception as e:
    st.error(f"❌ Failed to prepare NEW image: {e}")

col_e1, col_e2 = st.columns(2)

with col_e1:
    if old_bytes:
        st.download_button(
            label="⬇️ Download annotated OLD",
            data=old_bytes,
            file_name=f"annotated_old_{old_id}.png",
            mime="image/png",
            key=f"dl_old_final_{old_id}",
            use_container_width=True,
        )
        st.caption(f"📦 {len(old_bytes) / 1024:.1f} KB · {old_size[0]}×{old_size[1]} px")
    else:
        st.warning("OLD image not available.")

with col_e2:
    if new_bytes:
        st.download_button(
            label="⬇️ Download annotated NEW",
            data=new_bytes,
            file_name=f"annotated_new_{new_id}.png",
            mime="image/png",
            key=f"dl_new_final_{new_id}",
            use_container_width=True,
        )
        st.caption(f"📦 {len(new_bytes) / 1024:.1f} KB · {new_size[0]}×{new_size[1]} px")
    else:
        st.warning("NEW image not available.")