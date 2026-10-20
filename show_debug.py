s = open("utils/classify.py", "r", encoding="utf-8").read()
# Find the debug print
i = s.find("[DEBUG] emitting")
if i == -1:
    print("Debug print not found")
else:
    # Show 400 chars before and after
    print(s[max(0, i-400):i+400])