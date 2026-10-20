import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

old_block = '''    for c in comp_ids:
        best_func = None
        best_d = float("inf")
        for f in funcs:
            dist = _distance(c, f)
            if dist < best_d and dist <= comp_max_dist:
                best_func = f
                best_d = dist
        if best_func is not None:
            func_to_comps[id(best_func)].append(c)
            used_comps.add(id(c))'''

new_block = '''    for c in comp_ids:
        best_func = None
        best_d = float("inf")
        for f in funcs:
            dist = _distance(c, f)
            if dist < best_d:
                best_func = f
                best_d = dist
        if best_func is not None:
            func_to_comps[id(best_func)].append(c)
            used_comps.add(id(c))'''

if old_block in s:
    s2 = s.replace(old_block, new_block)
    p.write_text(s2, encoding="utf-8")
    print("FIXED. New length:", len(s2))
elif "if dist < best_d:" in s and "dist <= comp_max_dist" not in s:
    print("ALREADY fixed")
else:
    print("ERROR: target block not found. Showing context:")
    i = s.find("for c in comp_ids")
    print(s[i:i+500])