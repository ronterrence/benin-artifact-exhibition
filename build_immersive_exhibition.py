import os
import html
from pathlib import Path
import pandas as pd

BASE_DIR = Path("benin_output")
CSV_PATH = BASE_DIR / "artifact_manifest_enriched.csv"
PLATES_DIR = BASE_DIR / "plates"
OUT_DIR = BASE_DIR / "immersive_exhibition"

CLUSTER_NAMES_PATH = BASE_DIR / "cluster_names.csv"
import csv

import csv
import re

def load_cluster_names():
    if not CLUSTER_NAMES_PATH.exists():
        print("No cluster_names.csv found — using default labels.")
        return {}

    print("Reading cluster names from:", CLUSTER_NAMES_PATH.resolve())

    mapping = {}

    with open(CLUSTER_NAMES_PATH, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)

        rows = list(reader)

    if not rows:
        return {}

    print("cluster_names header:", rows[0])

    for row in rows[1:]:
        if not row:
            continue

        # If parsed correctly, row should be:
        # [cluster, suggested_name, top_terms, artifact_count]
        # If parsed badly, row[0] may contain the whole line.
        first = str(row[0]).strip()

        m = re.match(r"^\s*(\d+)", first)
        if not m:
            continue

        cluster_id = int(m.group(1))

        if len(row) >= 2 and row[1]:
            suggested_name = str(row[1]).strip()
        else:
            # fallback: extract quoted name from malformed single-cell row
            line = first
            quoted = re.findall(r'"([^"]+)"', line)
            if quoted:
                suggested_name = quoted[0].strip()
            else:
                suggested_name = f"Cluster {cluster_id}"

        mapping[cluster_id] = suggested_name

    return mapping
    
def load_wall_texts():
    path = BASE_DIR / "cluster_wall_texts.csv"

    if not path.exists():
        print("No cluster_wall_texts.csv found.")
        return {}

    df = pd.read_csv(path, encoding="utf-8-sig")

    mapping = {}
    for _, row in df.iterrows():
        cluster_id = int(row["cluster"])
        mapping[cluster_id] = str(row["wall_text"])

    return mapping
#def load_cluster_names():
#    if not CLUSTER_NAMES_PATH.exists():
#        print("No cluster_names.csv found — using default labels.")
#        return {}
#
#    df = pd.read_csv(CLUSTER_NAMES_PATH)
#
 #   mapping = {}
  #  for _, row in df.iterrows():
   #     mapping[int(row["cluster"])] = str(row["suggested_name"])

    #return mapping
#CLUSTER_LABELS = {
#   0: "Cluster 00",
#   1: "Cluster 01",
#   2: "Cluster 02",
#   3: "Cluster 03",
#   4: "Cluster 04",
#   5: "Cluster 05",
#   6: "Cluster 06",
#   7: "Cluster 07",
#   8: "Cluster 08",
#   9: "Cluster 09",
#   10: "Cluster 10",
# }

CLUSTER_NOTES = {
    0: "A visually related group generated from CLIP embeddings.",
    1: "A visually related group generated from CLIP embeddings.",
    2: "A visually related group generated from CLIP embeddings.",
    3: "A visually related group generated from CLIP embeddings.",
    4: "A visually related group generated from CLIP embeddings.",
    5: "A visually related group generated from CLIP embeddings.",
    6: "A visually related group generated from CLIP embeddings.",
    7: "A visually related group generated from CLIP embeddings.",
    8: "A visually related group generated from CLIP embeddings.",
    9: "A visually related group generated from CLIP embeddings.",
    10: "A visually related group generated from CLIP embeddings.",
}

INTRO = """
An immersive digital exhibition built from paired Benin artifact scans, CLIP-based visual grouping,
and catalog descriptions. Each room presents one visual family from the corpus.
""".strip()


def esc(x):
    if pd.isna(x):
        return ""
    return html.escape(str(x))


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def artifact_card(row, rel_plate_path):
    artifact_id = esc(row.get("artifact_id", ""))
    title = esc(row.get("title", "")) or artifact_id
    description = esc(row.get("description", ""))

    short_desc = description[:260] + ("..." if len(description) > 260 else "")

    return f"""
    <a class="artifact-card" href="artifact_pages/{artifact_id}.html">
      <img src="{rel_plate_path}" alt="{title}">
      <div class="artifact-overlay">
        <div class="artifact-id">{artifact_id}</div>
        <h3>{title}</h3>
        <p>{short_desc}</p>
      </div>
    </a>
    """


def main():
    cluster_names = load_cluster_names()
    wall_texts = load_wall_texts()
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    ensure_dir(OUT_DIR)

    sections = []
    nav_links = []

    grouped = df.sort_values(["cluster", "artifact_id"]).groupby("cluster")

    for cluster_id, group in grouped:
        #label = CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}")
        #cluster_names = load_cluster_names()
        label = cluster_names.get(cluster_id, f"Cluster {cluster_id}")
        note = CLUSTER_NOTES.get(cluster_id, "Visual grouping of related artifacts.")
        section_id = f"room-{cluster_id}"

        nav_links.append(f'<a href="#{section_id}">{esc(label)}</a>')

        cards = []
        for _, row in group.iterrows():
            artifact_id = str(row["artifact_id"]).strip().lower()
            plate_path = PLATES_DIR / f"{artifact_id}_plate.jpg"
            if not plate_path.exists():
                continue

            rel_plate_path = os.path.relpath(plate_path, OUT_DIR).replace("\\", "/")
            cards.append(artifact_card(row, rel_plate_path))

        if not cards:
            continue
        
        wall_text = wall_texts.get(cluster_id, note)
        
        sections.append(f"""
        <section class="room" id="{section_id}">
        <div class="room-header">
        <div class="room-number">Room {cluster_id}</div>
        <h2>{esc(label)}</h2>
        <p class="wall-text">{esc(wall_text)}</p>
        </div>
        <div class="room-grid">
            {''.join(cards)}
          </div>
        </section>
        """)

    css = """
    :root {
      --bg: #111111;
      --panel: #1a1a1a;
      --text: #f4f0e8;
      --muted: #b7ada1;
      --accent: #c08b48;
      --line: rgba(255,255,255,0.08);
    }
    .wall-text {
        max-width: 900px;
        line-height: 1.7;
        font-size: 1.05rem;
        color: #ddd2c4;
        margin-top: 10px;
    }
    .artifact-card {
        text-decoration: none;
        color: inherit;
    }
    * { box-sizing: border-box; }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
    }

    .hero {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: center;
      padding: 48px;
      background:
        linear-gradient(rgba(0,0,0,0.45), rgba(0,0,0,0.75)),
        radial-gradient(circle at top left, #4c3215, transparent 40%),
        radial-gradient(circle at bottom right, #2d2d2d, transparent 35%);
      border-bottom: 1px solid var(--line);
    }

    .hero h1 {
      margin: 0 0 16px;
      font-size: 3rem;
      max-width: 900px;
    }

    .hero p {
      max-width: 900px;
      color: var(--muted);
      font-size: 1.1rem;
      line-height: 1.7;
    }

    .hero-nav {
      margin-top: 28px;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }

    .hero-nav a {
      color: var(--text);
      text-decoration: none;
      border: 1px solid var(--line);
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.03);
    }

    .hero-nav a:hover {
      border-color: var(--accent);
      color: var(--accent);
    }

    .room {
      min-height: 100vh;
      padding: 42px 30px 54px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(180deg, #131313, #101010);
    }

    .room-header {
      max-width: 1100px;
      margin: 0 auto 24px;
    }

    .room-number {
      color: var(--accent);
      font-weight: bold;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 10px;
      font-size: 0.9rem;
    }

    .room-header h2 {
      margin: 0 0 10px;
      font-size: 2rem;
    }

    .room-header p {
      margin: 0;
      color: var(--muted);
      max-width: 900px;
      line-height: 1.6;
    }

    .room-grid {
      max-width: 1400px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 22px;
    }

    .artifact-card {
      position: relative;
      overflow: hidden;
      border-radius: 20px;
      background: var(--panel);
      border: 1px solid var(--line);
      min-height: 380px;
      box-shadow: 0 12px 40px rgba(0,0,0,0.28);
    }

    .artifact-card img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;
      transition: transform 0.5s ease;
    }

    .artifact-card:hover img {
      transform: scale(1.03);
    }

    .artifact-overlay {
      position: absolute;
      left: 0;
      right: 0;
      bottom: 0;
      padding: 20px 18px 18px;
      background: linear-gradient(180deg, rgba(0,0,0,0), rgba(0,0,0,0.82) 42%, rgba(0,0,0,0.95));
    }

    .artifact-id {
      font-size: 0.82rem;
      color: var(--accent);
      font-weight: bold;
      margin-bottom: 8px;
      letter-spacing: 0.05em;
    }

    .artifact-overlay h3 {
      margin: 0 0 8px;
      font-size: 1rem;
      line-height: 1.35;
    }

    .artifact-overlay p {
      margin: 0;
      color: #ddd2c4;
      font-size: 0.92rem;
      line-height: 1.45;
    }

    .footer {
      padding: 28px;
      text-align: center;
      color: var(--muted);
      background: #0d0d0d;
    }
    """

    html_doc = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Benin Immersive Exhibition</title>
      <style>{css}</style>
    </head>
    <body>
      <section class="hero">
        <h1>Benin Immersive Exhibition</h1>
        <p>{esc(INTRO)}</p>
        <div class="hero-nav">
          {''.join(nav_links)}
        </div>
      </section>

      {''.join(sections)}

      <div class="footer">
        Generated from paired plates, CLIP visual clustering, and enriched catalog metadata.
      </div>
    </body>
    </html>
    """

    out_file = OUT_DIR / "index.html"
    out_file.write_text(html_doc, encoding="utf-8")
    print(f"Saved immersive exhibition: {out_file}")


if __name__ == "__main__":
    main()