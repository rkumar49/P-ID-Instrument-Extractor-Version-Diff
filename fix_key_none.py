import pathlib

p = pathlib.Path("utils/diff.py")
s = p.read_text(encoding="utf-8")

# Update the fallback key builder to include the component prefix when func is None
old = '''    if cid and cid.lower() != "nan":
        norm_cid = _normalize_id(cid)
        return f"{norm_cid}|{func}|{fx},{fy}"
    # Fallback: only func + position
    return f"|{func}|{fx},{fy}"'''

new = '''    if cid and cid.lower() != "nan":
        norm_cid = _normalize_id(cid)
        # When func is None/empty, use just the component ID
        if not func:
            return f"{norm_cid}|{fx},{fy}"
        return f"{norm_cid}|{func}|{fx},{fy}"
    # No component_id — fallback to func + position
    return f"|{func}|{fx},{fy}"'''

if new in s:
    print("ALREADY patched")
elif old in s:
    s2 = s.replace(old, new)
    p.write_text(s2, encoding="utf-8")
    print("PATCHED. New length:", len(s2))
else:
    print("ERROR: target not found. Showing _key function:")
    i = s.find("def _key")
    j = s.find("\n\n", i)
    print(s[i:j])