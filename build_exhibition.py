import html
from pathlib import Path

import pandas as pd

BASE_DIR = Path("benin_output")
CSV_PATH = BASE_DIR / "artifact_manifest_enriched.csv"
ROOT_OUT = Path("index.html")
HTML_OUT_DIR = BASE_DIR / "html_exhibition"

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

INTRO_TEXT = (
    "A machine-assisted visual exhibition of Benin artifacts built from paired scans, "
    "CLIP similarity clustering, and catalog descriptions extracted from Pitt Rivers' "
    "Antique Works of Art from Benin."
)


def esc(x) -> str:
    if pd.isna(x):
        return ""
    return html.escape(str(x))


def build_card(row: pd.Series, img_path: str) -> str:
    title = esc(row.get("title", "Untitled"))
    desc = esc(str(row.get("description", ""))[:220])
    artifact_id = esc(row["artifact_id"])
    cluster = esc(row.get("cluster", ""))

    search_text = f"{artifact_id} {title} {desc}".lower()

    return f"""
    <article class="card" data-artifact="{artifact_id.lower()}" data-text="{search_text}">
      <img src="{img_path}" alt="{artifact_id}" onclick="openLightbox(this.src)">
      <div class="card-content">
        <div class="artifact-id">{artifact_id}</div>
        <div class="title">{title}</div>
        <div class="meta">Cluster: {cluster}</div>
        <div class="description">{desc}</div>
      </div>
    </article>
    """


def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    if "artifact_id" not in df.columns:
        raise ValueError("CSV must contain an 'artifact_id' column.")
    if "cluster" not in df.columns:
        raise ValueError("CSV must contain a 'cluster' column.")

    HTML_OUT_DIR.mkdir(parents=True, exist_ok=True)

    sections = []

    grouped = df.sort_values(["cluster", "artifact_id"]).groupby("cluster")
    for cluster_id, group in grouped:
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
    body {
      margin: 0;
      font-family: Georgia, serif;
      background: #0f0f0f;
      color: #eaeaea;
    }

    header {
      padding: 60px 40px;
      background: #111;
      border-bottom: 1px solid #222;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    h1 {
      margin: 0;
      font-size: 42px;
      font-weight: 500;
    }

    .subtitle {
      color: #aaa;
      margin-top: 10px;
      max-width: 800px;
      line-height: 1.6;
    }

    .toolbar {
      margin-top: 20px;
    }

    input[type="search"] {
      padding: 12px 14px;
      min-width: 320px;
      border: 1px solid #333;
      border-radius: 10px;
      background: #1a1a1a;
      color: #eee;
      font-size: 1rem;
    }

    main {
      max-width: 1600px;
      margin: 0 auto;
    }

    .cluster-section {
      padding: 60px 40px;
    }

    .section-header h2 {
      font-size: 28px;
      font-weight: 400;
      margin-bottom: 10px;
    }

    .section-header p {
      color: #888;
      margin-bottom: 30px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 40px;
    }

    .card {
      background: #151515;
      border: 1px solid #222;
      border-radius: 8px;
      overflow: hidden;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .card:hover {
      transform: translateY(-6px);
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .card img {
    width: 100%;
    display: block;
    background: #fff;
    filter: grayscale(100%);
    aspect-ratio: 1 / 1;
    object-fit: contain;
    }

    .card-content {
      padding: 20px;
    }

    .artifact-id {
      font-size: 12px;
      color: #888;
      margin-bottom: 6px;
    }

    .title {
      font-size: 22px;
      margin-bottom: 10px;
      line-height: 1.35;
    }

    .meta {
      font-size: 13px;
      color: #888;
      margin-bottom: 12px;
    }

    .description {
    font-size: 13px;
    color: #999;
    line-height: 1.6;
    max-height: 120px;
    overflow: hidden;
    }

    .hidden {
      display: none !important;
    }

    footer {
      padding: 40px;
      color: #888;
      text-align: center;
      border-top: 1px solid #222;
    }
    #lightbox {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.9);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    #lightbox img {
        max-width: 90%;
        max-height: 90%;
    }
    """
    

    js = """
    const searchBox = document.getElementById('searchBox');
    const cards = Array.from(document.querySelectorAll('.card'));
    const sections = Array.from(document.querySelectorAll('.cluster-section'));

    function applyFilter() {
      const q = searchBox.value.trim().toLowerCase();

      cards.forEach(card => {
        const hay = (card.dataset.text || '') + ' ' + (card.dataset.artifact || '');
        const show = !q || hay.includes(q);
        card.classList.toggle('hidden', !show);
      });

      sections.forEach(section => {
        const visibleCards = section.querySelectorAll('.card:not(.hidden)');
        section.classList.toggle('hidden', visibleCards.length === 0);
      });
    }
    function openLightbox(src) {
        const lb = document.getElementById('lightbox');
        const img = document.getElementById('lightbox-img');
        img.src = src;
        lb.style.display = 'flex';
    }

    function closeLightbox() {
        document.getElementById('lightbox').style.display = 'none';
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
        <div class="subtitle">{esc(INTRO_TEXT)}</div>
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
    <div id="lightbox" onclick="closeLightbox()">
        <img id="lightbox-img">
    </div>
    </body>
    </html>
    """

    ROOT_OUT.write_text(html_doc, encoding="utf-8")
    (HTML_OUT_DIR / "index.html").write_text(html_doc, encoding="utf-8")

    print(f"Saved exhibition: {ROOT_OUT}")
    print(f"Also saved copy: {HTML_OUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()