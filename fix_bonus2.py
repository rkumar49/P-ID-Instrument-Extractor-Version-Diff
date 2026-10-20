import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

old = "                    if d <= pipe_max_dist:\n                        cost[ci, pi] = d"
new = "                    if d <= pipe_max_dist:\n                        cost[ci, pi] = d - 500   # bonus for matching"

if new in s:
    print("ALREADY has bonus")
elif old in s:
    s2 = s.replace(old, new)
    p.write_text(s2, encoding="utf-8")
    print("PATCHED")
else:
    print("Looking for cost line...")
    for line in s.split("\n"):
        if "cost[" in line and "=" in line and "np.full" not in line:
            print(repr(line))