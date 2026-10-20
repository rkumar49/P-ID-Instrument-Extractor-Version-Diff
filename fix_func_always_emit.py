import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

# Find the current emission block
old_block = '''        if not comps:
            # No component for this func — assign nearest system code to the func itself
            best_sys = None
            best_sys_d = float("inf")
            for sc in sys_codes:
                dist = _distance(f, sc)
                if dist < best_sys_d and dist <= sys_max_dist:
                    best_sys = sc
                    best_sys_d = dist
                    print(f"[DEBUG] emitting bare func: {f['text_norm']} at ({f['x']}, {f['y']})")

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
        else:'''

new_block = '''        # ALWAYS emit the func itself as a bare row, regardless of components
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

        if comps:'''

if new_block in s:
    print("ALREADY patched")
elif old_block in s:
    s2 = s.replace(old_block, new_block)
    p.write_text(s2, encoding="utf-8")
    print("PATCHED. New length:", len(s2))
else:
    print("ERROR: target block not found. Showing context:")
    i = s.find("if not comps:")
    if i == -1:
        print("'if not comps:' not found")
    else:
        print(s[i:i+800])