import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

# Look for an existing patch marker
if "Renumber duplicate" in s:
    print("ALREADY patched in classify.py")
else:
    # Find the final sort line that ends group_instruments
    markers = [
        '    instruments.sort(key=lambda r: (r["y"] // 100, r["x"]))',
        "    instruments.sort(key=lambda r: (r['y'] // 100, r['x']))",
    ]
    found = None
    for m in markers:
        if m in s:
            found = m
            break

    if not found:
        print("ERROR: cannot find instruments.sort line")
        i = s.find("instruments.sort")
        print("Context:", s[max(0, i-100):i+200])
    else:
        new_sort = '''    # Renumber duplicate component IDs by position (top-to-bottom, left-to-right)
    from collections import defaultdict
    by_cid = defaultdict(list)
    for r in instruments:
        if r.get("component_id"):
            by_cid[r["component_id"]].append(r)

    for cid, group in by_cid.items():
        if len(group) > 1:
            group.sort(key=lambda r: (r["y"], r["x"]))
            for i, r in enumerate(group, start=1):
                r["component_id"] = f"{cid}_#{i}"

    instruments.sort(key=lambda r: (r["y"] // 100, r["x"]))
'''
        s2 = s.replace(found, new_sort)
        p.write_text(s2, encoding="utf-8")
        print("PATCHED. New length:", len(s2))