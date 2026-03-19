import os
import html
from pathlib import Path
import pandas as pd

BASE_DIR = Path("benin_output")
CSV_PATH = BASE_DIR / "artifact_manifest_enriched.csv"
PLATES_DIR = BASE_DIR / "plates"

#OUT_DIR = BASE_DIR / "html_exhibition"
OUT_DIR = Path(".")
ROOT_OUT = Path("index.html")
HTML_OUT_DIR = BASE_DIR / "html_exhibition"
HTML_OUT_DIR.mkdir(parents=True, exist_ok=True)
# Optional human-readable cluster labels
CLUSTER_LABELS = {
    0: "Cluster 00",
    1: "Cluster 01",
    2: "Cluster 02",
    3: "Cluster 03",
    4: "Cluster 04",
    5: "Cluster 05",
    6: "Cluster 06",
    7: "Cluster 07",
    8: "Cluster 08",
    9: "Cluster 09",
    10: "Cluster 10",
}

INTRO_TEXT = """
A machine-assisted visual exhibition of Benin artifacts built from paired scans,
CLIP similarity clustering, and catalog descriptions extracted from Pitt Rivers'
Antique Works of Art from Benin.
""".strip()


def esc(x):
    if pd.isna(x):
        return ""
    return html.escape(str(x))


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def build_card(row, rel_plate_path):
    artifact_id = esc(row.get("artifact_id", ""))
    title = esc(row.get("title", "")) or artifact_id
    description = esc(row.get("description", ""))
    cluster = esc(row.get("cluster", ""))

    return f"""
    <article class="card" data-artifact="{artifact_id.lower()}" data-text="{(title + ' ' + description).lower()}">
      <div class="card-image">
        <img src="{rel_plate_path}" alt="{title}">
      </div>
      <div class="card-body">
        <div class="artifact-id">{artifact_id}</div>
        <h3>{title}</h3>
        <div class="meta">Cluster: {cluster}</div>
        <p>{description}</p>
      </div>
    </article>
    """


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    if "artifact_id" not in df.columns:
        raise ValueError("CSV must contain an 'artifact_id' column.")

    if "cluster" not in df.columns:
        raise ValueError("CSV must contain a 'cluster' column.")

    ensure_dir(OUT_DIR)

    # Build cards grouped by cluster
    sections = []

    for cluster_id, group in df.sort_values(["cluster", "artifact_id"]).groupby("cluster"):
        label = CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}")

        cards = []
        for _, row in group.iterrows():
            artifact_id = str(row["artifact_id"]).strip().lower()
            plate_path = Path("benin_output") / "plates" / f"{artifact_id}_plate.jpg"

            if not plate_path.exists():
                continue

            rel_plate_path = plate_path.as_posix()
            cards.append(build_card(row, rel_plate_path))

    if cards:
            sections.append(f"""
            <section class="cluster-section" id="cluster-{cluster_id}">
              <div class="section-header">
                <h2>{esc(label)}</h2>
                <p>{len(cards)} artifacts</p>
              </div>
              <div class="grid">
                {''.join(cards)}
              </div>
            </section>
            """)

    css = """
    :root {
      --bg: #f5f1e8;
      --ink: #1d1a17;
      --muted: #6a625a;
      --card: #fffaf2;
      --line: #d8cfc3;
      --accent: #7a4d1d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }
    header {
      padding: 40px 24px 24px;
      border-bottom: 1px solid var(--line);
      background: #efe8dc;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    header h1 {
      margin: 0 0 8px;
      font-size: 2rem;
    }
    header p {
      margin: 0;
      max-width: 900px;
      color: var(--muted);
    }
    .toolbar {
      margin-top: 18px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    input[type="search"] {
      padding: 12px 14px;
      min-width: 320px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: white;
      font-size: 1rem;
    }
    main {
      padding: 24px;
      max-width: 1500px;
      margin: 0 auto;
    }
    .cluster-section {
      margin-bottom: 48px;
    }
    .section-header {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 18px;
    }
    .section-header h2 {
      margin: 0 0 10px;
      font-size: 1.4rem;
    }
    .section-header p {
      color: var(--muted);
      margin: 0 0 10px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 18px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 3px 10px rgba(0,0,0,.05);
    }
    .card-image {
      background: white;
      padding: 14px;
      border-bottom: 1px solid var(--line);
    }
    .card-image img {
      width: 100%;
      height: auto;
      display: block;
    }
    .card-body {
      padding: 14px 16px 18px;
    }
    .artifact-id {
      color: var(--accent);
      font-weight: bold;
      font-size: .9rem;
      margin-bottom: 6px;
    }
    .card h3 {
      margin: 0 0 8px;
      font-size: 1rem;
    }
    .meta {
      color: var(--muted);
      font-size: .9rem;
      margin-bottom: 10px;
    }
    .card p {
      margin: 0;
      font-size: .95rem;
    }
    .hidden {
      display: none !important;
    }
    footer {
      padding: 30px 24px 50px;
      color: var(--muted);
      text-align: center;
    }
    """

    js = """
    const searchBox = document.getElementById('searchBox');
    const cards = Array.from(document.querySelectorAll('.card'));
    const sections = Array.from(document.querySelectorAll('.cluster-section'));

    function applyFilter() {
      const q = searchBox.value.trim().toLowerCase();

      cards.forEach(card => {
        const hay = card.dataset.text + ' ' + card.dataset.artifact;
        const show = !q || hay.includes(q);
        card.classList.toggle('hidden', !show);
      });

      sections.forEach(section => {
        const visibleCards = section.querySelectorAll('.card:not(.hidden)');
        section.classList.toggle('hidden', visibleCards.length === 0);
      });
    }

    searchBox.addEventListener('input', applyFilter);
    """

    html_doc = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Benin Digital Exhibition</title>
      <style>{css}</style>
    </head>
    <body>
      <header>
        <h1>Benin Digital Exhibition</h1>
        <p>{esc(INTRO_TEXT)}</p>
        <div class="toolbar">
          <input id="searchBox" type="search" placeholder="Search by artifact ID, title, or description">
        </div>
      </header>

      <main>
        {''.join(sections)}
      </main>

      <footer>
        Generated from paired artifact plates, CLIP clusters, and catalog descriptions.
      </footer>

      <script>{js}</script>
    </body>
    </html>
    """

    #out_file = OUT_DIR / "index.html"
    #out_file.write_text(html_doc, encoding="utf-8")
    # write BOTH versions
    ROOT_OUT.write_text(html_doc, encoding="utf-8")
    (HTML_OUT_DIR / "index.html").write_text(html_doc, encoding="utf-8")
    
    #print(f"Saved exhibition: {out_file}")
    print(f"Saved exhibition: {ROOT_OUT}")
    print(f"Also saved copy: {HTML_OUT_DIR / 'index.html'}")

if __name__ == "__main__":
    main()