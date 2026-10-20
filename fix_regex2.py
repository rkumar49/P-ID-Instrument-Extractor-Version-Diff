import pathlib

p = pathlib.Path("utils/classify.py")
s = p.read_text(encoding="utf-8")

# The old narrow pattern
old = '''    "system_code":   re.compile(r"^=?\\s*H\\d{2}\\s*[A-Z]{2,}\\d*", re.IGNORECASE),'''

# Broader pattern — supports A, C, H, N, S, Z
new = '''    "system_code":   re.compile(r"^=?\\s*[ACHNSZ]\\d{2}\\s*[A-Z]{2,}\\d*", re.IGNORECASE),'''

if new in s:
    print("ALREADY fixed")
elif old in s:
    s2 = s.replace(old, new)
    p.write_text(s2, encoding="utf-8")
    print("FIXED. New length:", len(s2))
else:
    print("ERROR: target block not found")
    i = s.find("system_code")
    print("Context:")
    print(s[max(0, i-50):i+150])