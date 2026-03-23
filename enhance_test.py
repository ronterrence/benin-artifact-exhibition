from pathlib import Path
import numpy as np
from PIL import Image
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

SRC = Path("benin_output/plates")
DST = Path("benin_output/enhanced_plates")
MODEL_PATH = Path("weights/RealESRGAN_x2plus.pth")

DST.mkdir(parents=True, exist_ok=True)

model = RRDBNet(
    num_in_ch=3,
    num_out_ch=3,
    num_feat=64,
    num_block=23,
    num_grow_ch=32,
    scale=2,
)

upsampler = RealESRGANer(
    scale=2,
    model_path=str(MODEL_PATH),
    model=model,
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=False,
)

files = list(SRC.glob("*_plate.jpg"))

print(f"Processing {len(files)} images...\n")

for i, img_path in enumerate(files, 1):
    out_path = DST / img_path.name.replace("_plate", "_enhanced")

    if out_path.exists():
        print(f"[{i}] Skipping (exists): {img_path.name}")
        continue

    try:
        print(f"[{i}] Processing: {img_path.name}")

        img = Image.open(img_path).convert("RGB")
        img_np = np.array(img)

        output, _ = upsampler.enhance(img_np, outscale=2)

        Image.fromarray(output).save(out_path)

    except Exception as e:
        print(f"[{i}] ERROR: {img_path.name} -> {e}")

print("\nDone.")