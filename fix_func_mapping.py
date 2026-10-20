import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

# Find the line that assigns func to each instrument
old_line = '''                instruments.append({
                    "func": f["text_norm"], "func_det": f,
                    "system_code": best_sys["text_norm"] if best_sys else None,
                    "system_det": best_sys,
                    "component_id": c["text_norm"], "component_det": c,
                    "pipe_sizes": [p["text_norm"] for p in pipes],
                    "pipe_dets": pipes,
                    "confidence": conf,
                    "x": c["x"], "y": c["y"],
                    "w": c.get("w", 0), "h": c.get("h", 0),
                })'''

new_line = '''                # Only certain component prefixes get the func bubble's function.
                # QM/QN codes are stand-alone valves/tags; they don't belong to
                # any func bubble. Their func stays empty.
                COMPONENT_HAS_FUNC = (
                    "BG", "BP", "BL", "BX", "BS", "BC", "BQ",
                    "HN", "RM", "GP", "MA", "CM",
                )
                cid_prefix = str(c["text_norm"]).split("-")[0][:2].upper() if "-" in str(c["text_norm"]) else ""

                if cid_prefix in COMPONENT_HAS_FUNC:
                    assigned_func = f["text_norm"]
                    func_det = f
                else:
                    # QM/QN/etc — no func
                    assigned_func = None
                    func_det = None

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
                })'''

if "COMPONENT_HAS_FUNC" in s:
    print("ALREADY patched")
elif old_line in s:
    s2 = s.replace(old_line, new_line)
    p.write_text(s2, encoding="utf-8")
    print("PATCHED. New length:", len(s2))
else:
    print("ERROR: target block not found. Showing context:")
    i = s.find('"func": f["text_norm"]')
    print(s[max(0, i-200):i+500])