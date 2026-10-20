"""
Versions & Diff — browse saved documents and compare two versions.
"""

import io
import os
import sys

import pandas as pd
import streamlit as st

# Make project root importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.oracle import load_documents, load_instruments, delete_document
from utils.diff import compare_versions


st.set_page_config(page_title="Versions & Diff", page_icon="🔀", layout="wide")
st.title("🔀 Versions & Diff")

# ---- Load documents ----
try:
    docs = load_documents()
except Exception as e:
    st.error(f"Oracle error: {e}")
    st.stop()

if docs.empty:
    st.info("No documents saved yet. Save one from the main page first.")
    st.stop()

tab1, tab2 = st.tabs(["📚 Saved Versions", "🔀 Compare Two Versions"])

with tab1:
    st.dataframe(docs, use_container_width=True, hide_index=True)

    doc_id = st.selectbox(
        "Inspect a version",
        options=docs["DOC_ID"].tolist(),
        format_func=lambda x: f"#{x} — {docs[docs['DOC_ID']==x]['FILENAME'].iloc[0]}",
    )
    if doc_id:
        df = load_instruments(doc_id)
        st.write(f"**{len(df)}** instruments")
        st.dataframe(df, use_container_width=True, height=400)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇️ Download CSV",
                df.to_csv(index=False).encode("utf-8"),
                file_name=f"doc{doc_id}.csv",
            )
        with c2:
            if st.button(f"🗑️ Delete document #{doc_id}"):
                delete_document(doc_id)
                st.success(f"Deleted #{doc_id}")
                st.rerun()

with tab2:
    if len(docs) < 2:
        st.warning("Need at least 2 versions to compare.")
        st.stop()

    def label(row):
        return f"#{row['DOC_ID']} — {row['FILENAME']}"

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
            "🖳 New version",
            options=docs["DOC_ID"].tolist(),
            format_func=lambda x: label(docs[docs["DOC_ID"] == x].iloc[0]),
            index=0,
        )

    if old_id == new_id:
        st.warning("Pick two different versions.")
        st.stop()

    with st.expander("♙️ Position change threshold"):
        move_px = st.number_input("Move threshold (px)", 0, 2000, 50, 10)

    df_old = load_instruments(old_id)
    df_new = load_instruments(new_id)
    diff = compare_versions(df_old, df_new, move_threshold_px=int(move_px))

    counts = diff["Status"].value_counts().to_dict()
    m = st.columns(5)
    m[0].metric("➕ࠕ Added", counts.get("added", 0))
    m[1].metric("❌═ Deleted", counts.get("deleted", 0))
    m[2].metric("🔄 Modified", counts.get("modified", 0))
    m[3].metric("↔️ Moved", counts.get("moved", 0))
    m[4].metric("✅ Unchanged", counts.get("unchanged", 0))

    statuses = st.multiselect(
        "Show:",
        ["added", "deleted", "modified", "moved", "modified+moved", "unchanged"],
        default=["added", "deleted", "modified", "moved", "modified+moved"],
    )
    view = diff[diff["Status"].isin(statuses)]

    def color_row(row):
        c = {
            "added": "#d4edda", "deleted": "#f8d7da",
            "modified": "#fff3cd", "moved": "#cce5ff",
            "modified+moved": "#ffe0b2", "unchanged": "",
        }.get(row["Status"], "")
        return [f"background-color: {c}"] * len(row) if c else [""] * len(row)

    st.dataframe(view.style.apply(color_row, axis=1), use_container_width=True, height=500)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        diff.to_excel(w, sheet_name="Full Diff", index=False)
        for s in ["added", "deleted", "modified", "moved"]:
            sub = diff[diff["Status"] == s]
            if not sub.empty:
                sub.to_excel(w, sheet_name=s, index=False)

    st.download_button(
        "⬇️ Download diff (Excel)",
        data=buf.getvalue(),
        file_name=f"diff_{old_id}_vs_{new_id}.xlsx",
    )
