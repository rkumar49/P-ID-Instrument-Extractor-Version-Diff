import pathlib

p = pathlib.Path("utils/diff.py")
s = p.read_text(encoding="utf-8")

# Find the _key function and replace it entirely
i = s.find("def _key")
j = s.find("def compare_versions", i)

if i == -1 or j == -1:
    print("ERROR: _key not found")
else:
    new_key = '''def _key(row):
    """
    Component ID is now unique (duplicates renamed _#1, _#2).
    Rows without a component_id fall back to func + coarse position.
    """
    cid = str(row.get("component_id") or "").strip()
    if cid and cid.lower() != "nan":
        return _normalize_id(cid)
    func = str(row.get("func") or "").strip().upper()
    fx = int(row.get("x", 0) or 0) // 500
    fy = int(row.get("y", 0) or 0) // 500
    return f"|{func}|{fx},{fy}"


'''
    s2 = s[:i] + new_key + s[j:]
    p.write_text(s2, encoding="utf-8")
    print("PATCHED. New length:", len(s2))