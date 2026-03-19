import os
import csv
import math
import shutil
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional

from PIL import Image, ImageOps, ImageDraw, ImageFont


# =========================
# CONFIG
# =========================

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
THUMB_SIZE = (360, 360)
CONTACT_SHEET_COLUMNS = 4
CONTACT_SHEET_BG = "white"
CONTACT_SHEET_MARGIN = 30
CAPTION_HEIGHT = 90
DEFAULT_THEME = "Unassigned"

# For large archives, smaller batch sizes are easier to curate
MAX_IMAGES_PER_CHAPTER_FOLDER = 80

# HTML image width
HTML_THUMB_WIDTH = 260


# =========================
# HELPERS
# =========================

def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_images(folder: Path) -> List[Path]:
    return sorted(
        [p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS]
    )


def load_metadata(csv_path: Optional[Path]) -> Dict[str, dict]:
    if not csv_path or not csv_path.exists():
        return {}

    metadata = {}
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = (row.get("filename") or "").strip()
            if filename:
                metadata[filename] = row
    return metadata


def get_font(size: int = 20):
    # Tries common fonts, falls back to default
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size=size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> List[str]:
    words = text.split()
    lines = []
    current = ""

    for word in words:
        trial = word if not current else current + " " + word
        bbox = draw.textbbox((0, 0), trial, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def thumbnail_with_caption(img_path: Path, caption: str, thumb_size=(360, 360), caption_height=90) -> Image.Image:
    img = Image.open(img_path).convert("RGB")
    thumb = ImageOps.fit(img, thumb_size, method=Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", (thumb_size[0], thumb_size[1] + caption_height), "white")
    canvas.paste(thumb, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font_title = get_font(18)
    font_small = get_font(15)

    # Split caption into title + extra if separated by " | "
    parts = caption.split(" | ", 1)
    title = parts[0]
    extra = parts[1] if len(parts) > 1 else ""

    y = thumb_size[1] + 8
    margin_x = 10
    max_width = thumb_size[0] - 2 * margin_x

    for line in wrap_text(draw, title, font_title, max_width)[:2]:
        draw.text((margin_x, y), line, fill="black", font=font_title)
        y += 22

    if extra:
        for line in wrap_text(draw, extra, font_small, max_width)[:2]:
            draw.text((margin_x, y), line, fill="dimgray", font=font_small)
            y += 18

    return canvas


def chunked(items: List, size: int) -> List[List]:
    return [items[i:i + size] for i in range(0, len(items), size)]


# =========================
# CORE LOGIC
# =========================

def build_manifest(images: List[Path], metadata: Dict[str, dict], out_csv: Path) -> List[dict]:
    rows = []

    for idx, img_path in enumerate(images, start=1):
        row_meta = metadata.get(img_path.name, {})

        row = {
            "id": idx,
            "filename": img_path.name,
            "relative_path": str(img_path),
            "title": row_meta.get("title", img_path.stem),
            "period": row_meta.get("period", ""),
            "material": row_meta.get("material", ""),
            "type": row_meta.get("type", ""),
            "provenance": row_meta.get("provenance", ""),
            "current_location": row_meta.get("current_location", ""),
            "theme": row_meta.get("theme", DEFAULT_THEME) or DEFAULT_THEME,
            "caption": row_meta.get("caption", ""),
            "source": row_meta.get("source", ""),
        }
        rows.append(row)

    safe_mkdir(out_csv.parent)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    return rows


def copy_into_theme_chapters(manifest_rows: List[dict], source_root: Path, output_dir: Path) -> Dict[str, List[dict]]:
    grouped = defaultdict(list)
    for row in manifest_rows:
        grouped[row["theme"]].append(row)

    chapters_dir = output_dir / "chapters"
    safe_mkdir(chapters_dir)

    for theme, items in grouped.items():
        theme_folder = chapters_dir / sanitize_filename(theme)
        safe_mkdir(theme_folder)

        for batch_num, batch in enumerate(chunked(items, MAX_IMAGES_PER_CHAPTER_FOLDER), start=1):
            batch_folder = theme_folder / f"batch_{batch_num:02d}"
            safe_mkdir(batch_folder)

            for row in batch:
                src = Path(row["relative_path"])
                dst = batch_folder / src.name
                if src.exists():
                    shutil.copy2(src, dst)

    return grouped


def sanitize_filename(name: str) -> str:
    keep = []
    for ch in name:
        if ch.isalnum() or ch in ("-", "_", " "):
            keep.append(ch)
    return "".join(keep).strip().replace(" ", "_") or "untitled"


def generate_contact_sheets(grouped: Dict[str, List[dict]], output_dir: Path) -> None:
    contact_dir = output_dir / "contact_sheets"
    safe_mkdir(contact_dir)

    for theme, items in grouped.items():
        if not items:
            continue

        thumbs = []
        for row in items:
            img_path = Path(row["relative_path"])
            if not img_path.exists():
                continue

            caption_parts = [row["title"]]
            extra_bits = [x for x in [row["period"], row["material"], row["current_location"]] if x]
            if extra_bits:
                caption_parts.append(" / ".join(extra_bits))
            caption = " | ".join(caption_parts)

            try:
                thumbs.append(
                    thumbnail_with_caption(
                        img_path,
                        caption,
                        thumb_size=THUMB_SIZE,
                        caption_height=CAPTION_HEIGHT
                    )
                )
            except Exception as e:
                print(f"Skipping {img_path.name}: {e}")

        if not thumbs:
            continue

        cols = CONTACT_SHEET_COLUMNS
        rows = math.ceil(len(thumbs) / cols)

        tile_w = THUMB_SIZE[0]
        tile_h = THUMB_SIZE[1] + CAPTION_HEIGHT

        sheet_w = cols * tile_w + (cols + 1) * CONTACT_SHEET_MARGIN
        sheet_h = rows * tile_h + (rows + 1) * CONTACT_SHEET_MARGIN + 80

        sheet = Image.new("RGB", (sheet_w, sheet_h), CONTACT_SHEET_BG)
        draw = ImageDraw.Draw(sheet)
        title_font = get_font(30)
        draw.text((CONTACT_SHEET_MARGIN, 20), theme, fill="black", font=title_font)

        for i, thumb in enumerate(thumbs):
            r = i // cols
            c = i % cols
            x = CONTACT_SHEET_MARGIN + c * (tile_w + CONTACT_SHEET_MARGIN)
            y = 70 + CONTACT_SHEET_MARGIN + r * (tile_h + CONTACT_SHEET_MARGIN)
            sheet.paste(thumb, (x, y))

        out_path = contact_dir / f"{sanitize_filename(theme)}_contact_sheet.jpg"
        sheet.save(out_path, quality=95)
        print(f"Saved {out_path}")


def generate_html_exhibition(grouped: Dict[str, List[dict]], output_dir: Path, title: str = "Benin Artifacts Exhibition Draft") -> None:
    html_dir = output_dir / "html_exhibition"
    safe_mkdir(html_dir)

    html_path = html_dir / "index.html"

    css = """
    body { font-family: Arial, sans-serif; margin: 0; background: #f7f4ee; color: #222; }
    header { padding: 40px; background: #1f1b18; color: #fff; }
    main { padding: 30px; }
    section { margin-bottom: 60px; }
    h1, h2 { margin-top: 0; }
    .theme-note { max-width: 900px; color: #444; margin-bottom: 18px; }
    .grid { display: flex; flex-wrap: wrap; gap: 18px; }
    .card { background: #fff; border-radius: 10px; overflow: hidden; width: 300px; box-shadow: 0 2px 10px rgba(0,0,0,.08); }
    .card img { width: 100%; height: auto; display: block; }
    .card-body { padding: 12px; }
    .meta { color: #666; font-size: 0.92rem; line-height: 1.4; }
    .caption { margin-top: 8px; }
    footer { padding: 30px; color: #666; }
    """

    body_sections = []

    for theme, items in grouped.items():
        cards = []
        for row in items:
            img_path = Path(row["relative_path"])
            if not img_path.exists():
                continue

            rel_img = os.path.relpath(img_path.resolve(), html_dir.resolve())
            meta_parts = [x for x in [row["period"], row["material"], row["type"], row["current_location"]] if x]
            meta = " • ".join(meta_parts)

            caption = row["caption"] or ""
            source = row["source"] or ""

            cards.append(f"""
            <div class="card">
                <img src="{rel_img}" alt="{html_escape(row['title'])}">
                <div class="card-body">
                    <strong>{html_escape(row['title'])}</strong>
                    <div class="meta">{html_escape(meta)}</div>
                    <div class="caption">{html_escape(caption)}</div>
                    <div class="meta" style="margin-top:8px;"><em>{html_escape(source)}</em></div>
                </div>
            </div>
            """)

        section_html = f"""
        <section>
            <h2>{html_escape(theme)}</h2>
            <div class="grid">
                {''.join(cards)}
            </div>
        </section>
        """
        body_sections.append(section_html)

    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{html_escape(title)}</title>
      <style>{css}</style>
    </head>
    <body>
      <header>
        <h1>{html_escape(title)}</h1>
        <p>A draft exhibition structure generated from the image archive and metadata.</p>
      </header>
      <main>
        {''.join(body_sections)}
      </main>
      <footer>
        Generated for curatorial review. Verify all captions, chronology, and provenance before publication.
      </footer>
    </body>
    </html>
    """

    html_path.write_text(html, encoding="utf-8")
    print(f"Saved {html_path}")


def html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_curatorial_summary(manifest_rows: List[dict], output_dir: Path) -> None:
    theme_counts = Counter(row["theme"] for row in manifest_rows)
    type_counts = Counter(row["type"] for row in manifest_rows if row["type"])
    material_counts = Counter(row["material"] for row in manifest_rows if row["material"])

    summary_path = output_dir / "curatorial_summary.txt"
    lines = [
        "CURATORIAL SUMMARY",
        "==================",
        "",
        f"Total artifacts indexed: {len(manifest_rows)}",
        "",
        "Themes:",
    ]
    for theme, count in theme_counts.most_common():
        lines.append(f"  - {theme}: {count}")

    lines.append("")
    lines.append("Types:")
    for t, count in type_counts.most_common(20):
        lines.append(f"  - {t}: {count}")

    lines.append("")
    lines.append("Materials:")
    for m, count in material_counts.most_common(20):
        lines.append(f"  - {m}: {count}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {summary_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Arrange artifact images into an exhibition structure.")
    parser.add_argument("--images", required=True, help="Path to folder containing artifact images")
    parser.add_argument("--metadata", required=False, help="Path to metadata CSV")
    parser.add_argument("--output", default="exhibition_output", help="Output directory")
    args = parser.parse_args()

    images_dir = Path(args.images)
    metadata_csv = Path(args.metadata) if args.metadata else None
    output_dir = Path(args.output)

    if not images_dir.exists():
        raise FileNotFoundError(f"Images folder not found: {images_dir}")

    safe_mkdir(output_dir)

    images = list_images(images_dir)
    if not images:
        raise RuntimeError("No images found in the supplied folder.")

    metadata = load_metadata(metadata_csv)
    manifest = build_manifest(images, metadata, output_dir / "manifest.csv")
    grouped = copy_into_theme_chapters(manifest, images_dir, output_dir)

    generate_contact_sheets(grouped, output_dir)
    generate_html_exhibition(grouped, output_dir, title="Benin Artifacts Exhibition Draft")
    generate_curatorial_summary(manifest, output_dir)

    print("\nDone.")
    print(f"Artifacts indexed: {len(manifest)}")
    print(f"Output folder: {output_dir.resolve()}")


if __name__ == "__main__":
    main()