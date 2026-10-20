s = open("utils/classify.py", "r", encoding="utf-8").read()
print("HAS renumber block:", "Renumber duplicate" in s)
print("HAS _#suffix:", '_#{i}' in s or "_{}#" in s)