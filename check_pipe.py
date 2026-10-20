s = open("utils/classify.py", "r", encoding="utf-8").read()
print("HAS tight radius:", "tight_pipe_dist" in s)
print("HAS axis-aware distance:", "_pipe_dist" in s)
print("HAS old wide radius:", "pipe_max_dist" in s and "tight_pipe_dist" not in s)