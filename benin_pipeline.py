import os
import re
import math
import shutil
import argparse
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageOps, ImageDraw, ImageFont
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from tqdm import tqdm
from transformers import CLIPProcessor, CLIPModel


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
PAIR_PATTERN = re.compile(r"^(fig_\d+)(h?)\.(jpg|jpeg|png|webp|tif|tiff)$", re.IGNORECASE)


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def get_font(size: int = 20):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size=size)
    return ImageFont.load_default()


def sanitize_filename(name: str) -> str:
    cleaned = []
    for ch in str(name):
        if ch.isalnum() or ch in ("-", "_", " "):
            cleaned.append(ch)
    return "".join(cleaned).strip().replace(" ", "_") or "untitled"


def list_images(folder: Path):
    return sorted(
        [p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    )


def pair_artifacts(images_dir: Path):
    artifacts = defaultdict(dict)
    skipped = []

    all_images = list_images(images_dir)
    print(f"Total image files discovered: {len(all_images)}")

    for img_path in all_images:
        name = img_path.name.lower()

        if not name.startswith("fig_"):
            skipped.append(img_path.name)
            continue

        stem = img_path.stem.lower()

        if stem.endswith("h"):
            artifact_id = stem[:-1]
            artifacts[artifact_id]["detail"] = img_path
        else:
            artifact_id = stem
            artifacts[artifact_id]["main"] = img_path

    return dict(sorted(artifacts.items())), skipped

    print(f"Artifacts paired/found: {len(artifacts)}")

    sample = list(artifacts.items())[:10]
    if sample:
        print("Sample artifact pairs:")
        for k, v in sample:
            print(f"  {k}: {v}")
    else:
        print("No artifact pairs found.")

    return dict(sorted(artifacts.items())), skipped


def resize_to_height(img: Image.Image, target_height: int) -> Image.Image:
    ratio = target_height / img.height
    new_width = int(img.width * ratio)
    return img.resize((new_width, target_height), Image.Resampling.LANCZOS)
    
def create_single_plate(img_path: Path, output_path: Path, artifact_id: str, subtitle: str = "single view"):
    img = Image.open(img_path).convert("RGB")

    padding = 30
    title_height = 60

    canvas_w = img.width + padding * 2
    canvas_h = img.height + title_height + padding * 2

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)

    title_font = get_font(26)
    small_font = get_font(18)

    draw.text((padding, 15), artifact_id.upper(), fill="black", font=title_font)
    draw.text((padding, 45), subtitle, fill="dimgray", font=small_font)

    canvas.paste(img, (padding, title_height))
    canvas.save(output_path, quality=95)
    

def create_plate(main_path: Path, detail_path: Path, output_path: Path, artifact_id: str):
    img_main = Image.open(main_path).convert("RGB")
    img_detail = Image.open(detail_path).convert("RGB")

    target_height = max(img_main.height, img_detail.height)
    img_main = resize_to_height(img_main, target_height)
    img_detail = resize_to_height(img_detail, target_height)

    gap = 40
    padding = 30
    title_height = 60

    canvas_w = img_main.width + img_detail.width + gap + padding * 2
    canvas_h = target_height + title_height + padding * 2

    canvas = Image.new("RGB", (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)
    title_font = get_font(26)
    small_font = get_font(18)

    draw.text((padding, 15), artifact_id.upper(), fill="black", font=title_font)
    draw.text((padding, 45), "main view", fill="dimgray", font=small_font)
    draw.text((padding + img_main.width + gap, 45), "detail / alternate view", fill="dimgray", font=small_font)

    canvas.paste(img_main, (padding, title_height))
    canvas.paste(img_detail, (padding + img_main.width + gap, title_height))

    canvas.save(output_path, quality=95)


def make_thumbnail(img_path: Path, size=(280, 280), caption=""):
    img = Image.open(img_path).convert("RGB")
    thumb = ImageOps.fit(img, size, method=Image.Resampling.LANCZOS)

    caption_height = 50
    canvas = Image.new("RGB", (size[0], size[1] + caption_height), "white")
    canvas.paste(thumb, (0, 0))

    draw = ImageDraw.Draw(canvas)
    font = get_font(18)
    draw.text((10, size[1] + 12), caption, fill="black", font=font)

    return canvas


def make_contact_sheet(image_paths, captions, output_path: Path, title: str):
    if not image_paths:
        return

    thumbs = []
    for img_path, caption in zip(image_paths, captions):
        try:
            thumbs.append(make_thumbnail(img_path, caption=caption))
        except Exception as e:
            print(f"Skipping thumbnail for {img_path.name}: {e}")

    if not thumbs:
        return

    cols = 4
    rows = math.ceil(len(thumbs) / cols)
    margin = 25
    title_height = 70
    thumb_w, thumb_h = thumbs[0].size

    sheet_w = cols * thumb_w + (cols + 1) * margin
    sheet_h = rows * thumb_h + (rows + 1) * margin + title_height

    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = get_font(30)

    draw.text((margin, 20), title, fill="black", font=title_font)

    for i, thumb in enumerate(thumbs):
        r = i // cols
        c = i % cols
        x = margin + c * (thumb_w + margin)
        y = title_height + margin + r * (thumb_h + margin)
        sheet.paste(thumb, (x, y))

    sheet.save(output_path, quality=95)


def load_clip(device: str):
    model_name = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_name)
    model = CLIPModel.from_pretrained(model_name)
    model.to(device)
    model.eval()
    return processor, model


@torch.no_grad()
def embed_image(img_path: Path, processor, model, device: str):
    image = Image.open(img_path).convert("RGB")

    inputs = processor(images=image, return_tensors="pt")
    pixel_values = inputs["pixel_values"].to(device)

    vision_outputs = model.vision_model(pixel_values=pixel_values)
    pooled = vision_outputs.pooler_output
    image_features = model.visual_projection(pooled)

    image_features = image_features / torch.norm(image_features, dim=-1, keepdim=True)

    return image_features.cpu().numpy().reshape(-1)


def build_embeddings(artifacts, processor, model, device: str):
    artifact_ids = []
    vectors = []
    failures = []

    for artifact_id, paths in tqdm(artifacts.items(), desc="Embedding images"):
        if "main" not in paths:
            failures.append((artifact_id, "missing main image"))
            continue

        try:
            vec = embed_image(paths["main"], processor, model, device)
            vec = np.asarray(vec, dtype=np.float32).reshape(-1)

            if vec.size == 0:
                failures.append((artifact_id, "empty vector"))
                continue

            artifact_ids.append(artifact_id)
            vectors.append(vec)

        except Exception as e:
            failures.append((artifact_id, repr(e)))
            print(f"Embedding failed for {artifact_id}: {repr(e)}")

    print(f"\nEmbedded successfully: {len(vectors)}")
    print(f"Embedding failures: {len(failures)}")

    if failures:
        print("\nFirst 10 failures:")
        for artifact_id, err in failures[:10]:
            print(f"  {artifact_id}: {err}")

    if not vectors:
        raise RuntimeError("No embeddings could be created.")

    return artifact_ids, np.vstack(vectors)


def choose_cluster_count(n_items: int, requested: int | None):
    if requested is not None:
        return max(2, min(requested, n_items))
    guessed = max(4, min(12, round(math.sqrt(n_items / 2))))
    return min(guessed, n_items)


def cluster_embeddings(artifact_ids, vectors, n_clusters: int):
    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(vectors)
    return labels, model


def nearest_to_centroid(vectors, labels, kmeans_model, artifact_ids):
    representatives = {}
    for cluster_id in sorted(set(labels)):
        idxs = np.where(labels == cluster_id)[0]
        centroid = kmeans_model.cluster_centers_[cluster_id]
        dists = np.linalg.norm(vectors[idxs] - centroid, axis=1)
        best_local = idxs[np.argmin(dists)]
        representatives[cluster_id] = artifact_ids[best_local]
    return representatives


def export_manifest(artifacts, labels_map, out_csv: Path):
    rows = []
    for artifact_id, paths in artifacts.items():
        rows.append({
            "artifact_id": artifact_id,
            "main_image": paths.get("main", "").name if paths.get("main") else "",
            "detail_image": paths.get("detail", "").name if paths.get("detail") else "",
            "has_pair": bool(paths.get("main") and paths.get("detail")),
            "cluster": labels_map.get(artifact_id, ""),
        })

    df = pd.DataFrame(rows).sort_values(by="artifact_id")
    df.to_csv(out_csv, index=False)
    return df


def copy_cluster_outputs(artifacts, labels_map, output_dir: Path):
    clusters_dir = output_dir / "clusters"
    safe_mkdir(clusters_dir)

    grouped = defaultdict(list)
    for artifact_id, cluster_id in labels_map.items():
        grouped[cluster_id].append(artifact_id)

    for cluster_id, artifact_ids in grouped.items():
        cluster_folder = clusters_dir / f"cluster_{cluster_id:02d}"
        main_folder = cluster_folder / "main_images"
        detail_folder = cluster_folder / "detail_images"
        plate_folder = cluster_folder / "plates"

        safe_mkdir(main_folder)
        safe_mkdir(detail_folder)
        safe_mkdir(plate_folder)

        for artifact_id in sorted(artifact_ids):
            paths = artifacts[artifact_id]

            if "main" in paths:
                shutil.copy2(paths["main"], main_folder / paths["main"].name)
            if "detail" in paths:
                shutil.copy2(paths["detail"], detail_folder / paths["detail"].name)

            plate_src = output_dir / "plates" / f"{artifact_id}_plate.jpg"
            if plate_src.exists():
                shutil.copy2(plate_src, plate_folder / plate_src.name)

    return grouped


def create_cluster_contact_sheets(artifacts, grouped_clusters, output_dir: Path):
    sheets_dir = output_dir / "cluster_contact_sheets"
    safe_mkdir(sheets_dir)

    for cluster_id, artifact_ids in grouped_clusters.items():
        image_paths = []
        captions = []

        for artifact_id in sorted(artifact_ids):
            if "main" in artifacts[artifact_id]:
                image_paths.append(artifacts[artifact_id]["main"])
                captions.append(artifact_id)

        out_path = sheets_dir / f"cluster_{cluster_id:02d}_contact_sheet.jpg"
        make_contact_sheet(
            image_paths=image_paths,
            captions=captions,
            output_path=out_path,
            title=f"Cluster {cluster_id:02d}"
        )


def create_projection_plot(artifact_ids, vectors, labels_map, output_path: Path):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping projection plot.")
        return

    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(vectors)

    labels = [labels_map[aid] for aid in artifact_ids]
    unique_labels = sorted(set(labels))

    plt.figure(figsize=(10, 8))
    for label in unique_labels:
        idxs = [i for i, l in enumerate(labels) if l == label]
        plt.scatter(coords[idxs, 0], coords[idxs, 1], label=f"Cluster {label}", s=40)

    for i, aid in enumerate(artifact_ids[:30]):
        plt.text(coords[i, 0], coords[i, 1], aid, fontsize=8)

    plt.title("Benin Artifacts CLIP Embedding Projection")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=180)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Pair Benin artifact scans, create exhibition plates, and cluster with CLIP.")
    parser.add_argument("--images", required=True, help="Folder containing fig_### images")
    parser.add_argument("--output", default="benin_output", help="Output folder")
    parser.add_argument("--clusters", type=int, default=None, help="Number of clusters; default is auto")
    args = parser.parse_args()

    images_dir = Path(args.images)
    print(f"Scanning images folder: {images_dir.resolve()}")
    print(f"Folder exists: {images_dir.exists()}")
    output_dir = Path(args.output)

    if not images_dir.exists():
        raise FileNotFoundError(f"Images folder not found: {images_dir}")

    safe_mkdir(output_dir)
    safe_mkdir(output_dir / "plates")

    print("\n1. Pairing artifacts...")
    artifacts, skipped = pair_artifacts(images_dir)
    print("First 10 artifact entries:")
    for i, (artifact_id, paths) in enumerate(artifacts.items()):
        print(artifact_id, paths)
        if i >= 9:
            break
    print(f"Artifacts found: {len(artifacts)}")
    print(f"Skipped files: {len(skipped)}")

    print("\n2. Creating exhibition plates...")
    paired_count = 0
    single_count = 0

    for artifact_id, paths in tqdm(artifacts.items(), desc="Creating plates"):
        out_path = output_dir / "plates" / f"{artifact_id}_plate.jpg"

        try:
            # Case 1: both main and detail exist
            if "main" in paths and "detail" in paths:
                main_path = paths["main"]
                detail_path = paths["detail"]

                # If detail is an h-image, treat it as zoom/detail
                if detail_path.stem.endswith("h"):
                    # Use the zoomed/detail image as the hero plate
                    create_single_plate(detail_path, out_path, artifact_id, subtitle="detail view")
                    single_count += 1
                else:
                    # True alternate pair
                    create_plate(main_path, detail_path, out_path, artifact_id)
                    paired_count += 1

            # Case 2: only main exists
            elif "main" in paths:
                create_single_plate(paths["main"], out_path, artifact_id, subtitle="single view")
                single_count += 1

            # Case 3: only detail exists
            elif "detail" in paths:
                create_single_plate(paths["detail"], out_path, artifact_id, subtitle="detail view")
                single_count += 1

        except Exception as e:
            print(f"Plate failed for {artifact_id}: {e}")

    print(f"Two-panel plates created: {paired_count}")
    print(f"Single-image plates created: {single_count}")

    print(f"Plates created: {paired_count}")

    print("\n3. Loading CLIP model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    processor, clip_model = load_clip(device)

    print("\n4. Building embeddings from main images...")
    artifact_ids, vectors = build_embeddings(artifacts, processor, clip_model, device)

    n_clusters = choose_cluster_count(len(artifact_ids), args.clusters)
    print(f"\n5. Clustering into {n_clusters} groups...")
    labels, kmeans_model = cluster_embeddings(artifact_ids, vectors, n_clusters)

    labels_map = {artifact_id: int(label) for artifact_id, label in zip(artifact_ids, labels)}
    representatives = nearest_to_centroid(vectors, labels, kmeans_model, artifact_ids)

    print("\n6. Exporting manifest...")
    manifest_df = export_manifest(artifacts, labels_map, output_dir / "artifact_manifest.csv")

    print("\n7. Copying grouped outputs...")
    grouped_clusters = copy_cluster_outputs(artifacts, labels_map, output_dir)

    print("\n8. Creating cluster contact sheets...")
    create_cluster_contact_sheets(artifacts, grouped_clusters, output_dir)

    print("\n9. Creating embedding projection plot...")
    create_projection_plot(artifact_ids, vectors, labels_map, output_dir / "embedding_projection.png")

    print("\nCluster representatives:")
    for cluster_id in sorted(representatives):
        print(f"  Cluster {cluster_id:02d}: {representatives[cluster_id]}")

    summary_path = output_dir / "summary.txt"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("Benin Artifact Pipeline Summary\n")
        f.write("===============================\n\n")
        f.write(f"Total artifact IDs: {len(artifacts)}\n")
        f.write(f"Artifacts embedded: {len(artifact_ids)}\n")
        f.write(f"Paired exhibition plates created: {paired_count}\n")
        f.write(f"Clusters: {n_clusters}\n\n")
        f.write("Cluster representatives:\n")
        for cluster_id in sorted(representatives):
            f.write(f"  Cluster {cluster_id:02d}: {representatives[cluster_id]}\n")

    print("\nDone.")
    print(f"Output folder: {output_dir.resolve()}")


if __name__ == "__main__":
    main()