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
        featured_card = None

        for _, row in group.iterrows():
            artifact_id = str(row["artifact_id"]).strip().lower()
            plate_path = Path("benin_output") / "plates" / f"{artifact_id}_plate.jpg"

            if not plate_path.exists():
                continue

            rel_plate_path = plate_path.as_posix()
            card_html = build_card(row, rel_plate_path)

        if featured_card is None:
            featured_card = card_html
        else:
            cards.append(card_html)

        if cards:
            sections.append(f"""
            <section class="cluster-section" id="cluster-{cluster_id}">
  
              <div class="cluster-header">
                <h2>Cluster {cluster_id:02d}</h2>
                <p>{len(cards)+1} artifacts</p>
              </div>
              <div class="featured">
                {featured_card}
              </div>

              <div class="grid">
                {''.join(cards)}
              </div>

            </section>
            """)

    css = """
    body {
    margin: 0;
    font-family: "Georgia", serif;
    background: #0b0b0b;
    color: #eaeaea;
    }

    /* HERO */
    .hero {
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: #000;
    }

    .hero-inner {
    max-width: 700px;
    }

    .hero h1 {
    font-size: 48px;
    font-weight: 500;
    margin-bottom: 20px;
    }

    .hero-sub {
    color: #aaa;
    font-size: 16px;
    margin-bottom: 30px;
    }

    .enter-btn {
    color: white;
    text-decoration: none;
    border: 1px solid #444;
    padding: 12px 24px;
    border-radius: 30px;
    transition: 0.3s;
    }

    .enter-btn:hover {
    background: white;
    color: black;
    }

    /* CLUSTERS */
    .cluster-section {
    padding: 100px 60px;
    border-top: 1px solid #1a1a1a;
    }

    .cluster-header h2 {
      font-size: 28px;
      margin-bottom: 5px;
    }

    .cluster-header p {
      color: #777;
      margin-bottom: 40px;
    }

    /* FEATURED */
    .featured {
      max-width: 900px;
      margin-bottom: 60px;
    }

    .featured img {
      width: 100%;
      filter: grayscale(100%);
    }

    /* GRID */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 40px;
    }

    /* CARD */
    .card {
      background: #111;
      border: 1px solid #222;
      border-radius: 6px;
      overflow: hidden;
      transition: 0.3s;
    }

    .card:hover {
      transform: translateY(-6px);
    }

    .card img {
      width: 100%;
      display: block;
      filter: grayscale(100%);
    }

    .card-content {
      padding: 16px;
    }

    .artifact-id {
      font-size: 12px;
      color: #888;
    }

    .title {
      margin-top: 6px;
      font-size: 14px;
    }

    .description {
      margin-top: 8px;
      font-size: 12px;
      color: #aaa;
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

    #/* ✅ ADD THIS PART BELOW */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href'))
          .scrollIntoView({ behavior: 'smooth' });
      });
    });
    
    function closeLightbox() {
        document.getElementById('lightbox').style.display = 'none';
    }
    searchBox.addEventListener('input', applyFilter);
    """
    hero = f"""
    <section class="hero">
    <div class="hero-inner">
    <h1>Benin Digital Exhibition</h1>
    <p class="hero-sub">
      A machine-generated visual grouping of Benin artifacts based on image similarity.
    </p>
    <a href="#cluster-0" class="enter-btn">Enter Archive </a>
    </div>
    </section>
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
      {hero}
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