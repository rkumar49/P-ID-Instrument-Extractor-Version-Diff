import pathlib
import re

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

# Find the broken line (no indent, at the start of a line)
broken = "pipe_max_dist = 120   # fixed tight radius (was scale_factor * 1.0 — too generous)"
fixed = "    pipe_max_dist = 120   # fixed tight radius"

if broken in s:
    s2 = s.replace(broken, fixed)
    p.write_text(s2, encoding="utf-8")
    print("FIXED (replaced unindented line)")
elif fixed in s:
    print("ALREADY fixed")
else:
    # Look for any line that starts with pipe_max_dist and has no indent
    lines = s.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("pipe_max_dist"):
            lines[i] = "    " + line
            p.write_text("\n".join(lines), encoding="utf-8")
            print(f"FIXED (added indent on line {i+1}): {lines[i]}")
            break
    else:
        print("Could not find the broken line. Showing lines around line 100:")
        for i, line in enumerate(lines[95:110], start=96):
            print(f"{i}: {repr(line)}")