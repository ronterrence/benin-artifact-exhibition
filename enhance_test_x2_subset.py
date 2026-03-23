from pathlib import Path
import numpy as np
from PIL import Image
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

SRC = Path("benin_output/test_enhancement")
DST = Path("benin_output/test_enhancement_x2")
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

for img_path in files:
    print(f"Processing: {img_path.name}")

    img = Image.open(img_path).convert("RGB")
    img_np = np.array(img)

    output, _ = upsampler.enhance(img_np, outscale=2)

    out_path = DST / img_path.name.replace("_plate", "_x2")
    Image.fromarray(output).save(out_path)

print("\nDone.")