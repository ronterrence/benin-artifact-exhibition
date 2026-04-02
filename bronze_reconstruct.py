from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from scipy.ndimage import gaussian_filter, binary_opening, binary_closing

INPUT_DIR = Path("benin_output/enhanced_plates")
OUTPUT_DIR = Path("benin_output/bronze_output")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


# -----------------------------
# Bronze Mapping (CLEAN)
# -----------------------------
def subtle_bronze_map(gray_array: np.ndarray) -> np.ndarray:
    norm = gray_array.astype(np.float32) / 255.0

    # stabilize tones
    norm = np.clip((norm - 0.2) / 0.6, 0, 1)

    # slight material variation
    noise = np.random.normal(0, 0.015, gray_array.shape)
    norm = np.clip(norm + noise, 0, 1)

    shadow = np.array([70, 45, 25]) / 255.0
    mid = np.array([140, 100, 60]) / 255.0
    highlight = np.array([210, 170, 110]) / 255.0

    bronze = (
        shadow * (1 - norm)[..., None] +
        mid * norm[..., None] * (1 - norm[..., None]) +
        highlight * norm[..., None]
    )

    return np.clip(bronze, 0, 1)


# -----------------------------
# Optional patina (light)
# -----------------------------
def add_subtle_patina(bronze: np.ndarray, gray: np.ndarray) -> np.ndarray:
    variation = (gray.astype(np.float32) / 255.0) * 0.05
    bronze = bronze * (1 - variation[..., None])
    return np.clip(bronze, 0, 1)


# -----------------------------
# Main processing
# -----------------------------
def process_image(img_path: Path) -> None:
    img = Image.open(img_path).convert("RGB")

    # subtle enhancement
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=70, threshold=3))

    # grayscale
    gray = np.array(img.convert("L"))

    # bronze mapping
    bronze = subtle_bronze_map(gray)
    bronze = add_subtle_patina(bronze, gray)

    # -----------------------------
    # Background mask (CRITICAL)
    # -----------------------------
    mask = gray > 235
    mask = binary_opening(mask, structure=np.ones((3, 3)))
    mask = binary_closing(mask, structure=np.ones((5, 5)))
    mask = gaussian_filter(mask.astype(float), sigma=1.2) > 0.5

    # restore clean white background
    bronze[mask] = [1, 1, 1]

    # -----------------------------
    # Optional: reference color
    # -----------------------------
    try:
        ref = np.array(Image.open("reference.jpg").convert("RGB")) / 255.0
        mean_color = ref.mean(axis=(0, 1))
        bronze = bronze * 0.7 + mean_color * 0.3
        bronze = np.clip(bronze, 0, 1)
    except:
        pass  # skip if no reference image

    # -----------------------------
    # Blend back luminance (keeps realism)
    # -----------------------------
    bronze_img = Image.fromarray((bronze * 255).astype(np.uint8))
    lum = Image.fromarray(gray).convert("RGB")
    bronze_img = Image.blend(bronze_img, lum, alpha=0.18)

    # save
    out_name = img_path.name.replace("_enhanced.jpg", "_bronze.jpg")
    out_path = OUTPUT_DIR / out_name
    bronze_img.save(out_path, quality=95)

    print(f"Saved: {out_path}")


# -----------------------------
# Run all
# -----------------------------
def main():
    images = list(INPUT_DIR.glob("*_enhanced.jpg"))
    print(f"Found {len(images)} enhanced images.")

    for img_path in images:
        process_image(img_path)


if __name__ == "__main__":
    main()