"""Compare two versions of instrument data with three-pass matching."""

import math
import re
import pandas as pd


# ============================================================
# NORMALIZATION
# ============================================================
def _normalize_id(cid):
    """Normalize a component ID for matching."""
    if not cid:
        return ""
    s = str(cid).strip().upper()
    # Strip trailing L/H that OCR merged from alarm markers
    # (BG001-BG02L → BG001-BG02)
    s = re.sub(r"^([A-Z]{2,4}\d{2,4}\-[A-Z]{2,4}\d+)[LH]$", r"\1", s)
    # Strip leading '='
    if s.startswith("="):
        s = s[1:].strip()
    # OCR fixes: O → 0, I → 1 when next to digits
    s = re.sub(r"(?<=\d)O", "0", s)
    s = re.sub(r"O(?=\d)", "0", s)
    return s


def _normalize_syscode(sc):
    if not sc:
        return ""
    s = str(sc).strip().upper()
    s = s.lstrip("=").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _normalize_func(f):
    if not f:
        return ""
    return str(f).strip().upper()


def _center(row):
    return (int(row.get("x", 0) or 0), int(row.get("y", 0) or 0))


def _dist(a, b):
    ax, ay = _center(a)
    bx, by = _center(b)
    return math.hypot(ax - bx, ay - by)


# ============================================================
# ROW HELPERS
# ============================================================
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
        "W (old)": int((old or {}).get("w", 0) or 0) if old else "",
        "H (old)": int((old or {}).get("h", 0) or 0) if old else "",
        "W (new)": int((new or {}).get("w", 0) or 0) if new else "",
        "H (new)": int((new or {}).get("h", 0) or 0) if new else "",
        "ΔX": dx if dx is not None else "",
        "ΔY": dy if dy is not None else "",
        "Δ Dist": round(dist, 1) if dist is not None else "",
    }


def _content_changed(old, new):
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
    content_changed = _content_changed(old, new)
    dist = _dist(old, new)
    moved = dist >= move_threshold_px
    if content_changed and moved:
        return "modified+moved"
    if content_changed:
        return "modified"
    if moved:
        return "moved"
    return "unchanged"


# ============================================================
# MAIN COMPARISON
# ============================================================
def compare_versions(df_old, df_new, move_threshold_px=50):
    """
    Compare two instrument DataFrames.

    Three-pass matching:
      1. Exact (component_id, system_code) match
      2. Component_id + nearest position (handles position shifts)
      3. Bare funcs matched to nearby funcs with components (reduces false deletes)
    """
    if df_old is None or df_old.empty:
        df_old = pd.DataFrame(columns=[
            "func", "system_code", "component_id", "pipe_sizes", "x", "y",
        ])
    if df_new is None or df_new.empty:
        df_new = df_old.iloc[0:0].copy()

    old_rows = [dict(r) for _, r in df_old.iterrows()]
    new_rows = [dict(r) for _, r in df_new.iterrows()]

    for r in old_rows:
        r["_matched_new_idx"] = None
        r["_matched_to_other"] = False
    for r in new_rows:
        r["_matched_new_idx"] = None

    matched_new = set()
    results = []

    # ---------- PASS 1: exact (component_id, system_code) ----------
    for i, o in enumerate(old_rows):
        cid = _normalize_id(o.get("component_id"))
        sysc = _normalize_syscode(o.get("system_code"))
        if not cid:
            continue
        for j, n in enumerate(new_rows):
            if j in matched_new:
                continue
            if _normalize_id(n.get("component_id")) == cid \
               and _normalize_syscode(n.get("system_code")) == sysc:
                results.append(_row_dict(
                    o, n, _status(o, n, move_threshold_px),
                    dist=_dist(o, n),
                    dx=int(n.get("x", 0) or 0) - int(o.get("x", 0) or 0),
                    dy=int(n.get("y", 0) or 0) - int(o.get("y", 0) or 0),
                ))
                matched_new.add(j)
                o["_matched_new_idx"] = j
                break

    # ---------- PASS 2: component_id + nearest position ----------
    for i, o in enumerate(old_rows):
        if o["_matched_new_idx"] is not None:
            continue
        cid = _normalize_id(o.get("component_id"))
        if not cid:
            continue

        candidates = [
            (j, n) for j, n in enumerate(new_rows)
            if j not in matched_new
            and _normalize_id(n.get("component_id")) == cid
        ]
        if not candidates:
            continue

        best_j, best_n, best_d = None, None, float("inf")
        for j, n in candidates:
            d = _dist(o, n)
            if d < best_d:
                best_j, best_n, best_d = j, n, d

        results.append(_row_dict(
            o, best_n, _status(o, best_n, move_threshold_px),
            dist=best_d,
            dx=int(best_n.get("x", 0) or 0) - int(o.get("x", 0) or 0),
            dy=int(best_n.get("y", 0) or 0) - int(o.get("y", 0) or 0),
        ))
        matched_new.add(best_j)
        o["_matched_new_idx"] = best_j

    # ---------- PASS 3: bare funcs matched to nearby new funcs ----------
    # A "bare func" row has NO component_id but has a func.
    # These represent func bubbles whose component wasn't detected.
    # Match them to the nearest new row with the same func (bare or component).

    unmatched_old_bare_funcs = []
    for o in old_rows:
        if o["_matched_new_idx"] is not None:
            continue
        cid = _normalize_id(o.get("component_id"))
        func = _normalize_func(o.get("func"))
        if not cid and func:
            unmatched_old_bare_funcs.append(o)

    unmatched_new_funcs = []
    for j, n in enumerate(new_rows):
        if j in matched_new:
            continue
        func = _normalize_func(n.get("func"))
        if func:
            unmatched_new_funcs.append((j, n))

    for o in unmatched_old_bare_funcs:
        o_func = _normalize_func(o.get("func"))
        o_sys = _normalize_syscode(o.get("system_code"))

        best_j, best_n, best_score = None, None, float("inf")
        for j, n in unmatched_new_funcs:
            if j in matched_new:
                continue
            if _normalize_func(n.get("func")) != o_func:
                continue
            n_sys = _normalize_syscode(n.get("system_code"))
            # Same sys code preferred; else a large penalty
            sys_penalty = 0 if n_sys == o_sys else 1000
            score = _dist(o, n) + sys_penalty
            if score < best_score:
                best_score = score
                best_j, best_n = j, n

        if best_j is not None and best_score <= 800:
            matched_new.add(best_j)
            o["_matched_new_idx"] = best_j
            o["_matched_to_other"] = True

    # ---------- Remaining old → deleted ----------
    for o in old_rows:
        if o["_matched_new_idx"] is not None:
            continue
        results.append(_row_dict(o, None, "deleted"))

    # ---------- Remaining new → added ----------
    for j, n in enumerate(new_rows):
        if j in matched_new:
            continue
        results.append(_row_dict(None, n, "added"))

    # ---------- Sort ----------
    result = pd.DataFrame(results)
    order = {
        "added": 0, "deleted": 1, "modified+moved": 2,
        "modified": 3, "moved": 4, "unchanged": 5,
    }
    result["_ord"] = result["Status"].map(order).fillna(99)
    return result.sort_values(["_ord", "Component ID"]).drop(columns=["_ord"]).reset_index(drop=True)