import glob
import re
import subprocess

input_pattern = "*.mp3"
output_file = "merged.mp3"

def extract_number(filename):
    match = re.match(r"(\d+)-", filename)
    return int(match.group(1)) if match else float("inf")

files = sorted(glob.glob(input_pattern), key=extract_number)

if not files:
    print("No mp3 files found!")
    exit()

with open("list.txt", "w", encoding="utf-8") as f:
    for file in files:
        f.write(f"file '{file}'\n")

subprocess.run([
    "ffmpeg", "-f", "concat", "-safe", "0",
    "-i", "list.txt", "-c", "copy", output_file
])

print("Done! Saved as:", output_file)
