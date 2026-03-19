import re
import csv
from pdfminer.high_level import extract_text

pdf_path = "antiqueworksofar00pitt.pdf"

text = extract_text(pdf_path)

pattern = r"Fig[s]?\.?\s*(\d+)[\s—\-\.]+(.*?)(?=Fig|Figs|DESCRIPTION OF PLATE|$)"

matches = re.findall(pattern, text, re.DOTALL)

rows = []

for fig, desc in matches:
    fig_id = f"fig_{int(fig):03d}"
    desc = " ".join(desc.split())
    rows.append((fig_id, desc))

with open("benin_descriptions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["artifact_id", "description"])
    writer.writerows(rows)

print("Extracted descriptions:", len(rows))