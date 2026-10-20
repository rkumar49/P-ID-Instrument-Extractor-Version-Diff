import pathlib
import re

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

# Update _distance to use box centers (if it doesn't already)
old_center = '''def _center(det):
    return (det["x"] + det["w"] / 2, det["y"] + det["h"] / 2)'''

if old_center in s:
    print("_center already uses bbox center — checking pipe matching...")
else:
    print("WARNING: _center function different. Showing current:")
    i = s.find("def _center")
    j = s.find("def ", i + 10)
    print(s[i:j])

# Now check how pipe matching uses distance
i = s.find("for p in pipe_sizes:")
j = s.find("# --- Build instrument records", i)
if i == -1 or j == -1:
    print("ERROR: pipe matching block not found")
else:
    print("\n=== Current pipe matching block ===")
    print(s[i:j])