"""
Extract text DIRECTLY from a PDF's text layer.

If the PDF has a text layer (created by CAD software that exports text as
actual characters), this gives 100% accurate text with exact coordinates —
far better than OCR.

If the PDF has no text layer (text exported as vector outlines), returns [].
"""

import fitz  # PyMuPDF
import streamlit as st


@st.cache_data(show_spinner=False, max_entries=5)
def extract_text_from_pdf(pdf_bytes, page_num=0, dpi=300):
    """
    Extract text from a single PDF page with positions.

    Returns:
        list of dicts (same schema as run_ocr):
            {
                "text": str,
                "confidence": float,   # always 1.0 (from text layer)
                "bbox": [[x1,y1], [x2,y1], [x2,y2], [x1,y2]],
                "x": int, "y": int, "w": int, "h": int,
                "source": "pdf_text_layer"
            }

        Empty list if no text layer.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if page_num < 0 or page_num >= len(doc):
        doc.close()
        return []

    page = doc[page_num]

    # PDF coordinates are in points (72 DPI). Convert to match our render DPI.
    scale = dpi / 72.0

    # get_text("words") → list of (x0, y0, x1, y1, word, block_no, line_no, word_no)
    words = page.get_text("words")

    # Group words into lines (a "line" = same block_no + line_no)
    from collections import defaultdict
    lines = defaultdict(list)
    for w in words:
        x0, y0, x1, y1, text, block_no, line_no, word_no = w
        key = (block_no, line_no)
        lines[key].append({
            "x0": x0, "y0": y0, "x1": x1, "y1": y1,
            "text": text,
            "word_no": word_no,
        })

    results = []
    for key, ws in lines.items():
        # Sort by word_no to keep the correct order
        ws_sorted = sorted(ws, key=lambda w: w["word_no"])

        # Merge words into a single line of text
        line_text = " ".join(w["text"] for w in ws_sorted)

        # Bounding box of the whole line
        x0 = min(w["x0"] for w in ws_sorted)
        y0 = min(w["y0"] for w in ws_sorted)
        x1 = max(w["x1"] for w in ws_sorted)
        y1 = max(w["y1"] for w in ws_sorted)

        # Scale to DPI
        X0, Y0 = int(x0 * scale), int(y0 * scale)
        X1, Y1 = int(x1 * scale), int(y1 * scale)

        results.append({
            "text": line_text.strip(),
            "confidence": 1.0,
            "bbox": [[X0, Y0], [X1, Y0], [X1, Y1], [X0, Y1]],
            "x": X0, "y": Y0,
            "w": X1 - X0,
            "h": Y1 - Y0,
            "source": "pdf_text_layer",
        })

    doc.close()
    return results


@st.cache_data(show_spinner=False, max_entries=5)
def count_pdf_text_items(pdf_bytes, page_num=0):
    """Quick check: how many text items does the PDF contain?"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if page_num < 0 or page_num >= len(doc):
        doc.close()
        return 0
    n = len(doc[page_num].get_text("words"))
    doc.close()
    return n