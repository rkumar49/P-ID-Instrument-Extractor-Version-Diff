s = open("utils/classify.py", "r", encoding="utf-8").read()

print("HAS comp position:", 'c["x"]' in s)
print("HAS no distance limit:", "no distance limit" in s)
print("LEN:", len(s))