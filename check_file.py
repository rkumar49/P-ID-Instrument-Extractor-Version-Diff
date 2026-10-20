s = open("app/pages/3_Visual_Diff.py", encoding="utf-8").read()
print("LEN:", len(s))
print("HAS noise filter:", '"note", "noise"' in s)
print("HAS unique prefix:", "vis_visual_diff_dl" in s)
print("HAS on_click:", "on_click" in s)
print()
print("=== Lines containing 'noise' ===")
for i, line in enumerate(s.splitlines(), 1):
    if "noise" in line:
        print(f"{i}: {line}")