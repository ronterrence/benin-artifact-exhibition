from pathlib import Path
import html
import os
import pandas as pd

BASE = Path("benin_output")
CSV_PATH = BASE / "artifact_manifest_enriched.csv"
PLATES_DIR = BASE / "plates"
OUT_DIR = BASE / "immersive_exhibition"
DETAIL_DIR = OUT_DIR / "artifact_pages"

def esc(x):
    if pd.isna(x):
        return ""
    return html.escape(str(x))

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def main():
    df = pd.read_csv(CSV_PATH)
    ensure_dir(DETAIL_DIR)

    for _, row in df.iterrows():
        artifact_id = str(row["artifact_id"]).strip().lower()
        plate_path = PLATES_DIR / f"{artifact_id}_plate.jpg"
        if not plate_path.exists():
            continue

        title = esc(row.get("title", "")) or artifact_id
        description = esc(row.get("description", ""))
        cluster = esc(row.get("cluster", ""))

        rel_plate = os.path.relpath(plate_path, DETAIL_DIR).replace("\\", "/")

        same_cluster = df[df["cluster"] == row["cluster"]].copy()
        same_cluster = same_cluster[same_cluster["artifact_id"].astype(str).str.lower() != artifact_id].head(8)

        related_cards = []
        for _, r in same_cluster.iterrows():
            rid = str(r["artifact_id"]).strip().lower()
            r_plate = PLATES_DIR / f"{rid}_plate.jpg"
            if not r_plate.exists():
                continue
            rel_r_plate = os.path.relpath(r_plate, DETAIL_DIR).replace("\\", "/")
            r_title = esc(r.get("title", "")) or rid
            related_cards.append(f"""
            <a class="related-card" href="{rid}.html">
              <img src="{rel_r_plate}" alt="{r_title}">
              <div class="related-body">
                <div class="related-id">{rid}</div>
                <div class="related-title">{r_title}</div>
              </div>
            </a>
            """)

        page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #111111;
      --panel: #1a1a1a;
      --text: #f4f0e8;
      --muted: #b7ada1;
      --accent: #c08b48;
      --line: rgba(255,255,255,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--text);
    }}
    .wrap {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 24px 60px;
    }}
    a {{
      color: var(--accent);
      text-decoration: none;
    }}
    .topnav {{
      margin-bottom: 24px;
      color: var(--muted);
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 28px;
      align-items: start;
    }}
    .hero img {{
      width: 100%;
      display: block;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: white;
    }}
    .meta {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 22px;
    }}
    .artifact-id {{
      color: var(--accent);
      font-weight: bold;
      letter-spacing: 0.05em;
      margin-bottom: 10px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 2rem;
      line-height: 1.2;
    }}
    .cluster {{
      color: var(--muted);
      margin-bottom: 18px;
    }}
    .description {{
      line-height: 1.75;
      color: #ddd2c4;
      white-space: normal;
    }}
    .section-title {{
      margin: 42px 0 16px;
      font-size: 1.35rem;
    }}
    .related-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 16px;
    }}
    .related-card {{
      display: block;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow: hidden;
    }}
    .related-card img {{
      width: 100%;
      display: block;
      background: white;
    }}
    .related-body {{
      padding: 12px;
    }}
    .related-id {{
      color: var(--accent);
      font-size: 0.85rem;
      font-weight: bold;
      margin-bottom: 6px;
    }}
    .related-title {{
      color: var(--text);
      font-size: 0.95rem;
      line-height: 1.35;
    }}
    @media (max-width: 900px) {{
      .hero {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topnav">
      <a href="../index.html">← Back to exhibition</a>
    </div>

    <div class="hero">
      <div>
        <img src="{rel_plate}" alt="{title}">
      </div>
      <div class="meta">
        <div class="artifact-id">{artifact_id}</div>
        <h1>{title}</h1>
        <div class="cluster">Cluster {cluster}</div>
        <div class="description">{description}</div>
      </div>
    </div>

    <h2 class="section-title">Related artifacts from the same cluster</h2>
    <div class="related-grid">
      {''.join(related_cards)}
    </div>
  </div>
</body>
</html>
"""
        out_path = DETAIL_DIR / f"{artifact_id}.html"
        out_path.write_text(page, encoding="utf-8")

    print(f"Saved detail pages in: {DETAIL_DIR}")

if __name__ == "__main__":
    main()