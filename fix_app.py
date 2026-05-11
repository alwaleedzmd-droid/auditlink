"""Quick fix: truncate app.py at line 911 to remove duplicate helper functions."""
with open("app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Keep only up to line 910 (index 909), i.e. truncate everything from line 911 onward
clean_lines = lines[:910]

# Strip trailing blank lines then add single newline
while clean_lines and clean_lines[-1].strip() == "":
    clean_lines.pop()
clean_lines.append("\n")

with open("app.py", "w", encoding="utf-8") as f:
    f.writelines(clean_lines)

print(f"Done! app.py truncated to {len(clean_lines)} lines.")
