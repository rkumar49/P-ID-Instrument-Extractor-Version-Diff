"""Filter OCR text into recognizable P&ID tags and classify them."""
import re
from utils.legend import (
    describe_tag,
    KKS_RE, EQUIP_SCOPED_INSTRUMENT_RE, LINE_RE, SIMPLE_ISA_RE, DN_RE,
)


# Order matters: most specific / longest first
PATTERNS = [KKS_RE, LINE_RE, EQUIP_SCOPED_INSTRUMENT_RE, SIMPLE_ISA_RE, DN_RE]


def normalize_text(text: str) -> str:
    """Uppercase and strip spaces - helps pattern matching."""
    return text.upper().replace(" ", "").strip()


def find_tags_in_text(text: str):
    """Find all tag-like substrings in one OCR text block."""
    t = normalize_text(text)
    found = []

    for pattern in PATTERNS:
        for m in re.finditer(pattern, t):
            matched = m.group(0)
            # Skip if already contained in a longer match
            if not any(matched in f for f in found):
                found.append(matched)

    return list(dict.fromkeys(found))  # dedupe, preserve order


def extract_tags(ocr_results, min_confidence=0.3, keep_status=False):
    """
    Build a list of structured tag dicts from OCR results.
    """
    tags = []
    seen = set()

    for r in ocr_results:
        if r["confidence"] < min_confidence:
            continue
        for tag in find_tags_in_text(r["text"]):
            key = (tag, r["x"], r["y"])
            if key in seen:
                continue
            seen.add(key)

            info = describe_tag(tag)

            # Skip status labels unless asked
            if info["category"] == "Status Label" and not keep_status:
                continue

            tags.append({
                "tag": tag,
                "category": info["category"],
                "prefix": info["prefix"],
                "meaning": info["meaning"],
                "confidence": round(r["confidence"], 3),
                "x": r["x"],
                "y": r["y"],
                "w": r["w"],
                "h": r["h"],
                "bbox": r["bbox"],
            })

    # Sort top-to-bottom, then left-to-right
    tags.sort(key=lambda t: (t["y"] // 20, t["x"]))
    return tags
