"""Classification and spatial grouping of CAD text detections."""
import re
import math


def normalize_text(text):
    t = str(text or "").strip()
    if not t:
        return t
    if t.startswith("="):
        t = t[1:].strip()
    if t.isupper() and len(t) <= 40 and re.search(r"\d", t):
        t = t.replace("O", "0")
        t = re.sub(r"(?<=[A-Z])I(?=\d)", "1", t)
        t = re.sub(r"(?<=\d)I(?=[A-Z\d-])", "1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

PATTERNS = {
    "pipe_size":     re.compile(r"^DN\s*\d+$", re.IGNORECASE),
    "system_code":   re.compile(r"^=?\s*[ACHNSZ]\d{2}\s*[A-Z]{2,}\d*", re.IGNORECASE),
    "component_id":  re.compile(r"^[A-Z]{2,4}\d{2,4}[-–]\s*[A-Z]{2,4}\d*", re.IGNORECASE),
    "instrument_func": re.compile(r"^[A-Z]{2,4}$"),
}


def classify_text(text):
    t = normalize_text(text)
    if not t:
        return "noise"
    if PATTERNS["pipe_size"].match(t):
        return "pipe_size"
    if PATTERNS["system_code"].match(t):
        return "system_code"
    if PATTERNS["component_id"].match(t):
        return "component_id"
    if PATTERNS["instrument_func"].match(t) and t.isupper():
        return "instrument_func"
    if len(t.split()) >= 3:
        return "note"
    if t.isdigit():
        return "noise"
    if len(t) <= 2:
        return "noise"
    return "unknown"


def category_color(cat):
    return {
        "instrument_func": (0, 165, 255),
        "system_code":     (200, 0, 200),
        "component_id":    (255, 100, 0),
        "pipe_size":       (0, 180, 0),
        "note":            (128, 128, 128),
        "noise":           (200, 200, 200),
        "unknown":         (0, 0, 0),
    }.get(cat, (0, 0, 0))

def _center(det):
    return (det["x"] + det["w"] / 2, det["y"] + det["h"] / 2)


def _distance(d1, d2):
    cx1, cy1 = _center(d1)
    cx2, cy2 = _center(d2)
    return math.hypot(cx1 - cx2, cy1 - cy2)


def _image_scale(detections):
    if not detections:
        return 500
    max_x = max(d.get("x", 0) + d.get("w", 0) for d in detections)
    max_y = max(d.get("y", 0) + d.get("h", 0) for d in detections)
    return max(max_x, max_y) / 15


def group_instruments(detections, scale_factor=None):
    """
    Group detections into instrument records.

    Fixes:
        - Each instrument's X/Y is the COMPONENT's position, not the func's.
        - Each component gets at most ONE pipe (the nearest), not all in range.
    """
    for d in detections:
        d["text_norm"] = normalize_text(d.get("text", ""))
        d["category"] = classify_text(d["text_norm"])

    funcs = [d for d in detections if d["category"] == "instrument_func"]
    
    # DEBUG
    print(f"[DEBUG] funcs count: {len(funcs)}")
    for f in funcs:
      print(f"[DEBUG] func: {f['text_norm']} at ({f['x']}, {f['y']})")

    sys_codes = [d for d in detections if d["category"] == "system_code"]
    comp_ids = [d for d in detections if d["category"] == "component_id"]
    pipe_sizes = [d for d in detections if d["category"] == "pipe_size"]

    if not funcs:
        return [], []

    if scale_factor is None:
        scale_factor = _image_scale(detections)

    # Thresholds (tighter than before)
    comp_max_dist = scale_factor * 1.5   # how far a comp can be from its func
    sys_max_dist  = scale_factor * 2.0
    pipe_max_dist = 300   # generous radius; optimal assignment handles selection

    # --- Assign each component to nearest func ---
    used_comps = set()
    func_to_comps = {id(f): [] for f in funcs}

    for c in comp_ids:
        best_func = None
        best_d = float("inf")
        for f in funcs:
            dist = _distance(c, f)
            if dist < best_d:
                best_func = f
                best_d = dist
        if best_func is not None:
            func_to_comps[id(best_func)].append(c)
            used_comps.add(id(c))

    # --- Assign each pipe to its NEAREST component (only one) ---
    used_pipes = set()
    comp_to_pipe = {}

    # Build distance matrix
    comp_list = [c for clist in func_to_comps.values() for c in clist]
    pipe_list = list(pipe_sizes)

    if comp_list and pipe_list:
        try:
            from scipy.optimize import linear_sum_assignment
            import numpy as np

            # Build cost matrix (rows=components, cols=pipes)
            INF = 1e9
            cost = np.full((len(comp_list), len(pipe_list)), INF)
            for ci, c in enumerate(comp_list):
                for pi, p_ in enumerate(pipe_list):
                    d = _distance(p_, c)
                    if d <= pipe_max_dist:
                        cost[ci, pi] = d - 500   # bonus for matching

            # Solve optimal assignment
            row_ind, col_ind = linear_sum_assignment(cost)

            for ci, pi in zip(row_ind, col_ind):
                if cost[ci, pi] < INF:
                    comp_to_pipe[id(comp_list[ci])] = pipe_list[pi]
                    used_pipes.add(id(pipe_list[pi]))
        except ImportError:
            # Fallback to greedy if scipy not installed
            candidates = []
            for p_ in pipe_list:
                for c in comp_list:
                    d = _distance(p_, c)
                    if d <= pipe_max_dist:
                        candidates.append((d, id(p_), p_, c))
            candidates.sort(key=lambda x: x[0])

            used_comps = set()
            for d, pid, p_, c in candidates:
                if pid in used_pipes or id(c) in used_comps:
                    continue
                comp_to_pipe[id(c)] = p_
                used_pipes.add(pid)
                used_comps.add(id(c))

# --- Build instrument records ---
    instruments = []
    for f in funcs:
        comps = func_to_comps.get(id(f), [])
        print(f"[DEBUG] func={f['text_norm']} at ({f['x']}, {f['y']})  has {len(comps)} comps")

        # ALWAYS emit the func itself as a bare row, regardless of components
        best_sys = None
        best_sys_d = float("inf")
        for sc in sys_codes:
            dist = _distance(f, sc)
            if dist < best_sys_d and dist <= sys_max_dist:
                best_sys = sc
                best_sys_d = dist

        instruments.append({
            "func": f["text_norm"], "func_det": f,
            "system_code": best_sys["text_norm"] if best_sys else None,
            "system_det": best_sys,
            "component_id": None, "component_det": None,
            "pipe_sizes": [], "pipe_dets": [],
            "confidence": f["confidence"],
            "x": f["x"], "y": f["y"],
            "w": f.get("w", 0), "h": f.get("h", 0),
        })

        if comps:
            for c in comps:
                # PER-COMPONENT system code: find nearest to THIS component
                best_sys = None
                best_sys_d = float("inf")
                for sc in sys_codes:
                    dist = _distance(c, sc)
                    if dist < best_sys_d and dist <= sys_max_dist:
                        best_sys = sc
                        best_sys_d = dist

                pipe = comp_to_pipe.get(id(c))
                pipes = [pipe] if pipe else []
                conf = min(f["confidence"], c["confidence"])
                if best_sys:
                    conf = min(conf, best_sys["confidence"])
                # Only certain component prefixes get the func bubble's function.
                # QM/QN codes are stand-alone valves/tags; they don't belong to
                # any func bubble. Their func stays empty.
                
                #COMPONENT_HAS_FUNC = (
                    #"BG", "BP", "BL", "BX", "BS", "BC", "BQ",
                    #"HN", "RM", "GP", "MA", "CM",
                #)
                
                               
                # ----------------------------------------------------
                # Assign func: QM/QN/RM are standalone tags → no func.
                # Every other component (BP/BF/BG/BL/BX/...) inherits
                # its bubble's func.
                # ----------------------------------------------------
                NO_FUNC_PREFIXES = ("QM", "QN", "RM", "SN")

                cid_prefix = ""
                if "-" in str(c["text_norm"]):
                    cid_prefix = str(c["text_norm"]).split("-")[0][:2].upper()

                if cid_prefix in NO_FUNC_PREFIXES:
                    assigned_func = None
                    func_det = None
                else:
                    assigned_func = f["text_norm"]
                    func_det = f

                instruments.append({
                    "func": assigned_func, "func_det": func_det,
                    "system_code": best_sys["text_norm"] if best_sys else None,
                    "system_det": best_sys,
                    "component_id": c["text_norm"], "component_det": c,
                    "pipe_sizes": [p["text_norm"] for p in pipes],
                    "pipe_dets": pipes,
                    "confidence": conf,
                    "x": c["x"], "y": c["y"],
                    "w": c.get("w", 0), "h": c.get("h", 0),
                })

                
                

    # --- Unassigned ---
    unassigned = []
    for c in comp_ids:
        if id(c) not in used_comps:
            unassigned.append({
                "type": "component_id", "text": c["text_norm"],
                "confidence": c["confidence"], "x": c["x"], "y": c["y"],
            })
    for p in pipe_sizes:
        if id(p) not in used_pipes:
            unassigned.append({
                "type": "pipe_size", "text": p["text_norm"],
                "confidence": p["confidence"], "x": p["x"], "y": p["y"],
            })


    return instruments, unassigned
