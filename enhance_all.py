from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import cv2
import os

# ---- CONFIG ----
INPUT_DIR = "benin_output/plates"
OUTPUT_DIR = "benin_output/enhanced_plates"
MODEL_PATH = "weights/RealESRGAN_x2plus.pth"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- MODEL ----
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=23, num_grow_ch=32, scale=2)

upsampler = RealESRGANer(
    scale=2,
    model_path=MODEL_PATH,
    model=model,
    tile=0,        # increase if memory issues
    tile_pad=10,
    pre_pad=0,
    half=False
)

# ---- PROCESS LOOP ----
for filename in os.listdir(INPUT_DIR):
    if not filename.lower().endswith((".jpg", ".png", ".jpeg")):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(
        OUTPUT_DIR,
        filename.replace(".jpg", "_enhanced.jpg")
    )

    print(f"Processing: {filename}")

    img = cv2.imread(input_path, cv2.IMREAD_COLOR)

    if img is None:
        print(f"Skipped (error reading): {filename}")
        continue

    try:
        output, _ = upsampler.enhance(img, outscale=2)
        cv2.imwrite(output_path, output)
        print(f"Saved: {output_path}")

    except Exception as e:
        print(f"Error processing {filename}: {e}")