s = open("utils/classify.py", "r", encoding="utf-8").read()

# Find the component assignment loop
idx = s.find("for c in comp_ids")
if idx == -1:
    print("ERROR: 'for c in comp_ids' not found")
else:
    chunk = s[idx:idx+400]
    print("--- Component assignment loop ---")
    print(chunk)
    print()
    print("Has comp_max_dist limit:", "dist <= comp_max_dist" in chunk)
    print("Has pure nearest match:", "if dist < best_d:" in chunk)