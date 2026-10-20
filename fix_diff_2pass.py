import pathlib

content = '''"""Compare two versions of instrument data with two-pass matching.

Algorithm:
  Pass 1: match on (component_id, system_code) — exact pair.
  Pass 2: for remaining rows, match on component_id + nearest position.
  Remaining: added / deleted.

This handles:
  * Same component ID appearing twice with different system codes.
  * System code changes between revisions.
  * Component moving to a different position.
"""

import math
import re
import pandas as pd


# ---------- Normalization ----------

def _normalize_id(cid):
    if not cid:
        return ""
    s = str(cid).strip().upper()
    s = re.sub(r"[^A-Z0-9\\-]", "", s)
    s = re.sub(r"(?<=\\d)O", "0", s)
    s = re.sub(r"O(?=\\d)", "0", s)
    return s


def _normalize_syscode(sc):
    if not sc:
        return ""
    s = str(sc).strip().upper()
    s = s.lstrip("=").strip()
    s = re.sub(r"\\s+", " ", s)
    return s


def _center(row):
    return (int(row.get("x", 0) or 0), int(row.get("y", 0) or 0))


def _dist(a, b):
    ax, ay = _center(a)
    bx, by = _center(b)
    return math.hypot(ax - bx, ay - by)


# ---------- Row → output dict ----------

def _row_dict(old, new, status, dist=None, dx=None, dy=None):
    return {
        "Status": status,
        "Component ID": (
            (new or old).get("component_id", "") if (old or new) else ""
        ),
        "Func (old)": (old or {}).get("func", "") or "",
        "Func (new)": (new or {}).get("func", "") or "",
        "Sys (old)": _normalize_syscode((old or {}).get("system_code")) if old else "",
        "Sys (new)": _normalize_syscode((new or {}).get("system_code")) if new else "",
        "Pipe (old)": (old or {}).get("pipe_sizes", "") if old else "",
        "Pipe (new)": (new or {}).get("pipe_sizes", "") if new else "",
        "X (old)": int((old or {}).get("x", 0) or 0) if old else "",
        "Y (old)": int((old or {}).get("y", 0) or 0) if old else "",
        "X (new)": int((new or {}).get("x", 0) or 0) if new else "",
        "Y (new)": int((new or {}).get("y", 0) or 0) if new else "",
        "ΔX": dx if dx is not None else "",
        "ΔY": dy if dy is not None else "",
        "Δ Dist": round(dist, 1) if dist is not None else "",
    }


def _is_content_changed(old, new):
    return (
        (old.get("func") or "") != (new.get("func") or "")
        or _normalize_syscode(old.get("system_code"))
           != _normalize_syscode(new.get("system_code"))
        or (old.get("pipe_sizes") or "") != (new.get("pipe_sizes") or "")
    )


def _status(old, new, move_threshold_px):
    if old is None:
        return "added"
    if new is None:
        return "deleted"
    content_changed = _is_content_changed(old, new)
    dist = _dist(old, new)
    moved = dist >= move_threshold_px
    if content_changed and moved:
        return "modified+moved"
    if content_changed:
        return "modified"
    if moved:
        return "moved"
    return "unchanged"


# ---------- Main comparison ----------

def compare_versions(df_old, df_new, move_threshold_px=50):
    if df_old is None or df_old.empty:
        df_old = pd.DataFrame(columns=[
            "func", "system_code", "component_id", "pipe_sizes", "x", "y",
        ])
    if df_new is None or df_new.empty:
        df_new = df_old.iloc[0:0].copy()

    old_rows = df_old.to_dict("records")
    new_rows = df_new.to_dict("records")

    matched_new = set()
    results = []

    # ---------- PASS 1: exact (component_id + system_code) ----------
    for o in old_rows:
        cid = _normalize_id(o.get("component_id"))
        sysc = _normalize_syscode(o.get("system_code"))
        if not cid:
            continue
        for j, n in enumerate(new_rows):
            if j in matched_new:
                continue
            if _normalize_id(n.get("component_id")) == cid \\
               and _normalize_syscode(n.get("system_code")) == sysc:
                results.append(_row_dict(o, n, _status(o, n, move_threshold_px),
                                         dist=_dist(o, n),
                                         dx=int(n.get("x", 0) or 0) - int(o.get("x", 0) or 0),
                                         dy=int(n.get("y", 0) or 0) - int(o.get("y", 0) or 0)))
                matched_new.add(j)
                o["_matched"] = True
                break

    # ---------- PASS 2: match on component_id + nearest position ----------
    for o in old_rows:
        if o.get("_matched"):
            continue
        cid = _normalize_id(o.get("component_id"))
        if not cid:
            continue
        # Find all unmatched new rows with this component ID
        candidates = [
            (j, n) for j, n in enumerate(new_rows)
            if j not in matched_new
            and _normalize_id(n.get("component_id")) == cid
        ]
        if not candidates:
            continue
        # Pick the nearest one
        best_j, best_n, best_d = None, None, float("inf")
        for j, n in candidates:
            d = _dist(o, n)
            if d < best_d:
                best_j, best_n, best_d = j, n, d
        results.append(_row_dict(o, best_n, _status(o, best_n, move_threshold_px),
                                 dist=best_d,
                                 dx=int(best_n.get("x", 0) or 0) - int(o.get("x", 0) or 0),
                                 dy=int(best_n.get("y", 0) or 0) - int(o.get("y", 0) or 0)))
        matched_new.add(best_j)
        o["_matched"] = True

    # ---------- Remaining old → deleted ----------
    for o in old_rows:
        if not o.get("_matched"):
            results.append(_row_dict(o, None, "deleted"))

    # ---------- Remaining new → added ----------
    for j, n in enumerate(new_rows):
        if j not in matched_new:
            results.append(_row_dict(None, n, "added"))

    result = pd.DataFrame(results)
    order = {
        "added": 0, "deleted": 1, "modified+moved": 2,
        "modified": 3, "moved": 4, "unchanged": 5,
    }
    result["_ord"] = result["Status"].map(order).fillna(99)
    return result.sort_values(["_ord", "Component ID"]).drop(columns=["_ord"]).reset_index(drop=True)
'''

pathlib.Path("utils/diff.py").write_text(content, encoding="utf-8")
print("Written", len(content), "chars to utils/diff.py")