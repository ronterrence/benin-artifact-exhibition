import html
from pathlib import Path

import pandas as pd

BASE_DIR = Path("benin_output")
CSV_PATH = BASE_DIR / "artifact_manifest_enriched.csv"
ROOT_OUT = Path("index.html")
HTML_OUT_DIR = BASE_DIR / "html_exhibition"
ARTIFACT_PAGES_DIR = HTML_OUT_DIR / "artifact_pages"

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
    <a class="card" href="benin_output/html_exhibition/artifact_pages/{artifact_id}.html"
       data-artifact="{artifact_id.lower()}" data-text="{search_text}">
      <img src="{img_path}" alt="{artifact_id}">
      <div class="card-content">
        <div class="artifact-id">{artifact_id}</div>
        <div class="title">{title}</div>
        <div class="meta">Cluster: {cluster}</div>
        <div class="description">{desc}</div>
      </div>
    </a>
    """

def build_artifact_page(row: pd.Series, related_rows: pd.DataFrame) -> str:
    artifact_id = esc(row.get("artifact_id", ""))
    title = esc(row.get("title", "Untitled")) or artifact_id
    description = esc(row.get("description", ""))
    cluster = int(row["cluster"])

    original_path = f"../../plates/{artifact_id.lower()}_plate.jpg"
    enhanced_path = f"../../enhanced_plates/{artifact_id.lower()}_enhanced.jpg"
    
    has_enhanced = Path(
    f"benin_output/enhanced_plates/{artifact_id.lower()}_enhanced.jpg"
    ).exists()

    plate_path = enhanced_path if Path(
        f"benin_output/enhanced_plates/{artifact_id.lower()}_enhanced.jpg"
    ).exists() else original_path

    related_cards = []
    for _, rel in related_rows.iterrows():
        rel_id = str(rel["artifact_id"]).strip().lower()
        if rel_id == artifact_id.lower():
            continue

        rel_title = esc(rel.get("title", rel_id))
        rel_img = f"../../plates/{rel_id}_plate.jpg"
        related_cards.append(f"""
        <a class="related-card" href="{rel_id}.html">
          <img src="{rel_img}" alt="{rel_id}">
          <div class="related-meta">
            <div class="artifact-id">{esc(rel_id)}</div>
            <div class="title">{rel_title}</div>
          </div>
        </a>
        """)

    related_html = "".join(related_cards[:8])

    css = """
    body {
      margin: 0;
      font-family: Georgia, serif;
      background: #0b0b0b;
      color: #eaeaea;
    }
    .page {
      max-width: 1200px;
      margin: 0 auto;
      padding: 48px 24px 80px;
    }
    .back {
      display: inline-block;
      margin-bottom: 24px;
      color: #bbb;
      text-decoration: none;
    }
    .hero {
      display: grid;
      grid-template-columns: 1.1fr 1fr;
      gap: 32px;
      align-items: start;
      margin-bottom: 48px;
    }
    .hero img {
      width: 100%;
      background: white;
      display: block;
      border-radius: 8px;
    }
    .meta {
      color: #999;
      margin-bottom: 12px;
    }
    h1 {
      margin: 0 0 16px;
      font-size: 2.2rem;
      line-height: 1.2;
    }
    .description {
      color: #cfcfcf;
      line-height: 1.8;
      font-size: 1rem;
    }
    h2 {
      margin-top: 56px;
      margin-bottom: 18px;
      font-size: 1.4rem;
    }
    .related-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 18px;
    }
    .related-card {
      text-decoration: none;
      color: inherit;
      background: #151515;
      border: 1px solid #222;
      border-radius: 8px;
      overflow: hidden;
    }
    .related-card img {
      width: 100%;
      display: block;
      background: white;
    }
    .related-meta {
      padding: 12px;
    }
    .artifact-id {
      font-size: 12px;
      color: #999;
      margin-bottom: 6px;
    }
    .title {
      font-size: 14px;
      line-height: 1.4;
    }
    @media (max-width: 900px) {
      .hero {
        grid-template-columns: 1fr;
      }
    }
    """

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{title}</title>
      <style>{css}</style>
    </head>
    <body>
      <div class="page">
        <a class="back" href="../../../index.html#cluster-{cluster:02d}">← Back to exhibition</a>
        <div class="hero">
          <div class="image-compare">
            <div class="image-panel">
                <h3>Original scan</h3>
                <img src="{original_path}" alt="{artifact_id} original">
                
           </div>
           
           {"<div class='image-panel'><h3>AI-enhanced</h3><img src='" + enhanced_path + "' alt='" + artifact_id + " enhanced'></div>" if has_enhanced else ""}
            </div>
           {"<p class='ai-note'>The enhanced image is an AI-assisted restoration for legibility and comparison. The original scan remains the primary archival reference.</p>" if has_enhanced else ""}
          <div>
            <div class="meta">Artifact: {artifact_id}</div>
            <div class="meta">Cluster: {cluster}</div>
            <h1>{title}</h1>
            <div class="description">{description}</div>
          </div>
        </div>

        <h2>Related artifacts in this cluster</h2>
        <div class="related-grid">
          {related_html}
        </div>
      </div>
    </body>
    </html>
    """    
def main() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    cluster_ids = sorted(df["cluster"].dropna().astype(int).unique())
    first_cluster_anchor = f"cluster-{cluster_ids[0]:02d}" if cluster_ids else "cluster-00"

    if "artifact_id" not in df.columns:
        raise ValueError("CSV must contain an 'artifact_id' column.")
    if "cluster" not in df.columns:
        raise ValueError("CSV must contain a 'cluster' column.")

    HTML_OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PAGES_DIR.mkdir(parents=True, exist_ok=True)
 
    sections = []

    grouped = df.sort_values(["cluster", "artifact_id"]).groupby("cluster")
    for cluster_id, group in grouped:
        print(f"Building cluster {cluster_id} with {len(group)} rows")
        label = CLUSTER_LABELS.get(cluster_id, f"Cluster {cluster_id}")
        cards = []
        featured_card = None

        for _, row in group.iterrows():
            artifact_id = str(row["artifact_id"]).strip().lower()
            plate_path = Path("benin_output") / "plates" / f"{artifact_id}_plate.jpg"

            if not plate_path.exists():
                print(f"Missing plate: {plate_path}")
                continue

            rel_plate_path = plate_path.as_posix()
            card_html = build_card(row, rel_plate_path)

            if featured_card is None:
                featured_card = card_html
            else:
                cards.append(card_html)

        print(f"Cluster {cluster_id}: featured_card set = {featured_card is not None}, extra cards = {len(cards)}")

        if featured_card is not None:
            sections.append(f"""
            <section class="cluster-section" id="cluster-{cluster_id:02d}">
              <div class="cluster-header">
                <h2>Cluster {cluster_id:02d}</h2>
                <p>{1 + len(cards)} artifacts</p>
              </div>

              <div class="featured">
                {featured_card}
              </div>

              <div class="grid">
                {''.join(cards)}
              </div>
            </section>
            """)

    print(f"Total sections built: {len(sections)}")

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
    .card {
      text-decoration: none;
      color: inherit;
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
    .hidden {
      display: none !important;
    }

    .description {
      margin-top: 8px;
      font-size: 12px;
      color: #aaa;
    }
    html {
  scroll-behavior: smooth;
    }

    .toolbar {
      margin-top: 18px;
      margin-bottom: 18px;
      display: flex;
      justify-content: center;
    }

    .toolbar input[type="search"] {
      width: min(520px, 90vw);
      padding: 12px 16px;
      border: 1px solid #333;
      border-radius: 10px;
      background: #141414;
      color: #eee;
      font-size: 1rem;
      outline: none;
    }

    .toolbar input[type="search"]::placeholder {
      color: #888;
    }

    .enter-btn {
      display: inline-block;
      margin-top: 8px;
    }

    .hidden {
      display: none !important;
    }
    .image-compare {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 40px;
    }

    .image-panel h3 {
      margin: 0 0 10px;
      font-size: 0.95rem;
      color: #aaa;
      font-weight: normal;
      letter-spacing: 0.02em;
    }

    .image-panel img {
      width: 100%;
      display: block;
      background: white;
      border-radius: 8px;
    }

    .ai-note {
      margin-top: 12px;
      color: #aaa;
      font-size: 0.92rem;
      line-height: 1.5;
    }

    @media (max-width: 900px) {
      .image-compare {
        grid-template-columns: 1fr;
      }
    }
    """

    js = """
    const searchBox = document.getElementById('searchBox');
    const cards = Array.from(document.querySelectorAll('.card'));
    const sections = Array.from(document.querySelectorAll('.cluster-section'));

    function applyFilter() {
      const q = (searchBox.value || '').trim().toLowerCase();

      cards.forEach(card => {
        const hay = ((card.dataset.text || '') + ' ' + (card.dataset.artifact || '')).toLowerCase();
        const show = !q || hay.includes(q);
        card.classList.toggle('hidden', !show);
      });

      sections.forEach(section => {
        const visibleCards = section.querySelectorAll('.card:not(.hidden)');
        section.classList.toggle('hidden', visibleCards.length === 0);
      });
    }

    if (searchBox) {
      searchBox.addEventListener('input', applyFilter);
    }

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
          target.scrollIntoView({ behavior: 'smooth' });
        }
      });
    });

    function openLightbox(src) {
      const lb = document.getElementById('lightbox');
      const img = document.getElementById('lightbox-img');
      if (!lb || !img) return;
      img.src = src;
      lb.style.display = 'flex';
    }

    function closeLightbox() {
      const lb = document.getElementById('lightbox');
      if (lb) lb.style.display = 'none';
    }
    
    function enterArchive(e) {
      e.preventDefault();
      
      if (searchBox) {
      searchBox.value = '';
      applyFilter();
    }

      const target = document.querySelector(e.currentTarget.getAttribute('href'));
      if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
      }
    }
    """

    hero = f"""
    <section class="hero">
      <div class="hero-inner">
        <h1>Benin Digital Exhibition</h1>
        <p class="hero-sub">
          A machine-generated visual grouping of Benin artifacts based on image similarity.
        </p>
        <div class="toolbar">
          <input id="searchBox" type="search" placeholder="Search by artifact ID, title, or description">
        </div>
        <a href="#{first_cluster_anchor}" class="enter-btn" onclick="enterArchive(event)">Enter Archive ↓</a>
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
    # Build artifact detail pages
    for _, row in df.iterrows():
        artifact_id = str(row["artifact_id"]).strip().lower()
        cluster = row["cluster"]

        plate_path = Path("benin_output") / "plates" / f"{artifact_id}_plate.jpg"
        if not plate_path.exists():
            continue

        related_rows = df[df["cluster"] == cluster].sort_values("artifact_id")
        page_html = build_artifact_page(row, related_rows)

        page_path = ARTIFACT_PAGES_DIR / f"{artifact_id}.html"
        page_path.write_text(page_html, encoding="utf-8")
        
    ROOT_OUT.write_text(html_doc, encoding="utf-8")
    (HTML_OUT_DIR / "index.html").write_text(html_doc, encoding="utf-8")

    print(f"Saved exhibition: {ROOT_OUT}")
    print(f"Also saved copy: {HTML_OUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()