"""
Text Diff — compare EVERY raw detection between two versions.
Not grouped into instruments.
"""

import io
import os
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.oracle import load_documents, load_detections


st.set_page_config(page_title="Text Diff", page_icon="📄", layout="wide")
st.title("📄 Raw Text Diff")
st.caption(
    "Compares EVERY detected text (not just grouped instruments). "
    "Shows added / deleted / moved text between two versions."
)

# ---- Load documents ----
try:
    docs = load_documents()
except Exception as e:
    st.error(f"Oracle error: {e}")
    st.stop()

if docs.empty:
    st.info("No documents saved yet. Save one from the main page first.")
    st.stop()

if len(docs) < 2:
    st.warning("Need at least 2 saved versions to compare.")
    st.stop()

# ---- Pick versions ----
def label(row):
    v = str(row.get("VERSION_LABEL") or "")
    f = str(row.get("FILENAME") or "")
    return f"#{row['DOC_ID']} — {v} ({f})"

c1, c2 = st.columns(2)
with c1:
    old_id = st.selectbox(
        "🕐 Old version",
        options=docs["DOC_ID"].tolist(),
        format_func=lambda x: label(docs[docs["DOC_ID"] == x].iloc[0]),
        index=len(docs) - 1,
    )
with c2:
    new_id = st.selectbox(
        "🆕 New version",
        options=docs["DOC_ID"].tolist(),
        format_func=lambda x: label(docs[docs["DOC_ID"] == x].iloc[0]),
        index=0,
    )

if old_id == new_id:
    st.warning("Pick two different versions.")
    st.stop()

# ---- Thresholds ----
with st.expander("⚙️ Matching settings"):
    tc1, tc2 = st.columns(2)
    with tc1:
        pos_tol = st.number_input(
            "Position tolerance (px)",
            min_value=5, max_value=500, value=100, step=10,
            help="Two identical texts within this distance count as 'same position'.",
        )
    with tc2:
        norm = st.checkbox(
            "Normalize text before comparing",
            value=True,
            help="Fix common OCR errors (O→0, I→1) before matching.",
        )

# ---- Load detections ----
old_dets = load_detections(old_id)
new_dets = load_detections(new_id)

st.write(f"**Old (doc #{old_id}):** {len(old_dets)} detections · "
         f"**New (doc #{new_id}):** {len(new_dets)} detections")

if old_dets.empty and new_dets.empty:
    st.warning("No detections found for either version. Did you save detections too?")
    st.stop()


# ---- Helper: normalize text ----
def _norm(t):
    if not norm:
        return str(t or "").strip()
    t = str(t or "").strip()
    if t.startswith("="):
        t = t[1:].strip()
    if t.isupper() and len(t) <= 40:
        t = t.replace("O", "0")
    return t


# ---- Prepare keys ----
# Each detection gets a key of (normalized_text, coarse_position)
def make_key(text, x, y, w, h):
    cx = int(x) + int(w) // 2
    cy = int(y) + int(h) // 2
    return (_norm(text), cx, cy)


old_keys = []
for _, r in old_dets.iterrows():
    old_keys.append({
        "key": make_key(r["TEXT_RAW"], r["X"], r["Y"], r.get("W", 0), r.get("H", 0)),
        "text": _norm(r["TEXT_RAW"]),
        "x": int(r["X"]), "y": int(r["Y"]),
        "category": r.get("CATEGORY", ""),
        "confidence": float(r.get("CONFIDENCE", 0)),
    })

new_keys = []
for _, r in new_dets.iterrows():
    new_keys.append({
        "key": make_key(r["TEXT_RAW"], r["X"], r["Y"], r.get("W", 0), r.get("H", 0)),
        "text": _norm(r["TEXT_RAW"]),
        "x": int(r["X"]), "y": int(r["Y"]),
        "category": r.get("CATEGORY", ""),
        "confidence": float(r.get("CONFIDENCE", 0)),
    })


# ---- Match: same text, position within tolerance ----
def match_detections(old_list, new_list, tol_px):
    used_new = set()
    results = []

    for o in old_list:
        best_idx = None
        best_dist = float("inf")
        for i, n in enumerate(new_list):
            if i in used_new:
                continue
            if o["text"] != n["text"]:
                continue
            dist = ((o["x"] - n["x"]) ** 2 + (o["y"] - n["y"]) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_idx = i
        if best_idx is not None and best_dist <= tol_px:
            n = new_list[best_idx]
            dx = n["x"] - o["x"]
            dy = n["y"] - o["y"]
            status = "moved" if (abs(dx) > 5 or abs(dy) > 5) else "unchanged"
            results.append({
                "Text": o["text"],
                "Status": status,
                "Category (old)": o["category"],
                "Category (new)": n["category"],
                "X (old)": o["x"], "Y (old)": o["y"],
                "X (new)": n["x"], "Y (new)": n["y"],
                "ΔX": dx, "ΔY": dy,
                "Δ Dist": round(best_dist, 1),
            })
            used_new.add(best_idx)
        else:
            # Try position-only match (same text, but far away)
            pos_match = None
            for i, n in enumerate(new_list):
                if i in used_new:
                    continue
                if o["text"] == n["text"]:
                    pos_match = i
                    break
            if pos_match is not None:
                n = new_list[pos_match]
                dx = n["x"] - o["x"]
                dy = n["y"] - o["y"]
                results.append({
                    "Text": o["text"],
                    "Status": "moved-far",
                    "Category (old)": o["category"],
                    "Category (new)": n["category"],
                    "X (old)": o["x"], "Y (old)": o["y"],
                    "X (new)": n["x"], "Y (new)": n["y"],
                    "ΔX": dx, "ΔY": dy,
                    "Δ Dist": round(((dx ** 2 + dy ** 2) ** 0.5), 1),
                })
                used_new.add(pos_match)
            else:
                results.append({
                    "Text": o["text"],
                    "Status": "deleted",
                    "Category (old)": o["category"],
                    "Category (new)": "",
                    "X (old)": o["x"], "Y (old)": o["y"],
                    "X (new)": "", "Y (new)": "",
                    "ΔX": "", "ΔY": "", "Δ Dist": "",
                })

    # Remaining new entries = added
    for i, n in enumerate(new_list):
        if i not in used_new:
            results.append({
                "Text": n["text"],
                "Status": "added",
                "Category (old)": "",
                "Category (new)": n["category"],
                "X (old)": "", "Y (old)": "",
                "X (new)": n["x"], "Y (new)": n["y"],
                "ΔX": "", "ΔY": "", "Δ Dist": "",
            })

    return pd.DataFrame(results)


diff = match_detections(old_keys, new_keys, int(pos_tol))

# ---- Summary ----
counts = diff["Status"].value_counts().to_dict()

st.markdown("### 📊 Summary")
m = st.columns(5)
m[0].metric("➕ Added", counts.get("added", 0))
m[1].metric("❌ Deleted", counts.get("deleted", 0))
m[2].metric("↔️ Moved (near)", counts.get("moved", 0))
m[3].metric("↔️ Moved (far)", counts.get("moved-far", 0))
m[4].metric("✅ Unchanged", counts.get("unchanged", 0))

# ---- Filter ----
statuses = st.multiselect(
    "Show:",
    ["added", "deleted", "moved", "moved-far", "unchanged"],
    default=["added", "deleted", "moved", "moved-far"],
)
view = diff[diff["Status"].isin(statuses)]

# ---- Color coding ----
def color_row(row):
    c = {
        "added": "#d4edda",
        "deleted": "#f8d7da",
        "moved": "#cce5ff",
        "moved-far": "#ffe0b2",
        "unchanged": "",
    }.get(row["Status"], "")
    return [f"background-color: {c}"] * len(row) if c else [""] * len(row)

st.markdown("### 📋 Diff (every detection)")
if view.empty:
    st.info("No rows match your filter.")
else:
    st.dataframe(view.style.apply(color_row, axis=1), use_container_width=True, height=600)

# ---- Category-level summary ----
'''
st.markdown("### 🗂️ Changes by category")
if not view.empty:
    cat_counts = view.groupby(["Category (old)", "Status"]).size().unstack(fill_value=0)
    st.dataframe(cat_counts, use_container_width=True)
'''

st.markdown("### 🗂️ Changes by category")

if not view.empty:
    # Merge old and new category (some rows only have one side)
    view["Category"] = view["Category (old)"].fillna("").replace("", None)
    view["Category"] = view["Category"].fillna(view["Category (new)"])

    # Pivot: category vs status
    pivot = view.groupby(["Category", "Status"]).size().unstack(fill_value=0)

    # Add totals
    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("Total", ascending=False)

    st.dataframe(pivot, use_container_width=True)

    # Show added values by category — the manager wants to see this
    st.markdown("### ➕ Added values (sample)")
    added_rows = diff[diff["Status"] == "added"]
    if not added_rows.empty:
        added_by_cat = added_rows.groupby("Category (new)").apply(
            lambda g: ", ".join(g["Text"].head(10).tolist()) + ("..." if len(g) > 10 else "")
        )
        for cat, texts in added_by_cat.items():
            with st.expander(f"**{cat}** — {len(added_rows[added_rows['Category (new)'] == cat])} items"):
                st.write(texts)
    else:
        st.info("No added values.")

    # Same for deleted
    st.markdown("### ❌ Deleted values (sample)")
    deleted_rows = diff[diff["Status"] == "deleted"]
    if not deleted_rows.empty:
        deleted_by_cat = deleted_rows.groupby("Category (old)").apply(
            lambda g: ", ".join(g["Text"].head(10).tolist()) + ("..." if len(g) > 10 else "")
        )
        for cat, texts in deleted_by_cat.items():
            with st.expander(f"**{cat}** — {len(deleted_rows[deleted_rows['Category (old)'] == cat])} items"):
                st.write(texts)
    else:
        st.info("No deleted values.")


# ---- Export ----
st.markdown("### 📥 Export")
buf = io.BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as w:
    diff.to_excel(w, sheet_name="Text Diff", index=False)
    for s in ["added", "deleted", "moved", "moved-far", "unchanged"]:
        sub = diff[diff["Status"] == s]
        if not sub.empty:
            sub.to_excel(w, sheet_name=s, index=False)

st.download_button(
    "⬇️ Download text diff (Excel)",
    data=buf.getvalue(),
    file_name=f"textdiff_{old_id}_vs_{new_id}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)