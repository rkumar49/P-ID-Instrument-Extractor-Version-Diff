import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

old_block = '''    used_pipes = set()
    comp_to_pipe = {}   # one pipe per component
    all_comps = [c for clist in func_to_comps.values() for c in clist]

    for p in pipe_sizes:
        best_comp = None
        best_d = float("inf")
        for c in all_comps:
            if id(c) in comp_to_pipe:
                continue   # this comp already has a pipe
            dist = _distance(p, c)
            if dist < best_d and dist <= pipe_max_dist:
                best_comp = c
                best_d = dist
        if best_comp is not None:
            comp_to_pipe[id(best_comp)] = p
            used_pipes.add(id(p))'''

new_block = '''    used_pipes = set()
    comp_to_pipe = {}   # one pipe per component
    all_comps = [c for clist in func_to_comps.values() for c in clist]

    # Tighter radius: pipes must be very close to their component
    tight_pipe_dist = scale_factor * 0.25   # ~166px for a 10000px image

    def _pipe_dist(pipe, comp):
        """Distance, halved if pipe shares an axis with the component."""
        dx = abs(pipe["x"] - comp["x"])
        dy = abs(pipe["y"] - comp["y"])
        base = (dx * dx + dy * dy) ** 0.5
        # Prefer pipes that are horizontally or vertically aligned
        if dx < 40 or dy < 40:
            return base * 0.5
        return base

    for p in pipe_sizes:
        best_comp = None
        best_d = float("inf")
        for c in all_comps:
            if id(c) in comp_to_pipe:
                continue   # this comp already has a pipe
            d = _pipe_dist(p, c)
            if d < best_d and d <= tight_pipe_dist:
                best_comp = c
                best_d = d
        if best_comp is not None:
            comp_to_pipe[id(best_comp)] = p
            used_pipes.add(id(p))'''

if "tight_pipe_dist" in s:
    print("ALREADY patched")
elif old_block in s:
    s2 = s.replace(old_block, new_block)
    p.write_text(s2, encoding="utf-8")
    print("PATCHED. New length:", len(s2))
else:
    print("ERROR: still no match")
    # Show the exact block char by char to see hidden differences
    i = s.find("used_pipes = set()")
    j = s.find("# --- Build instrument records ---", i)
    print("---ACTUAL BLOCK---")
    print(repr(s[i:j]))