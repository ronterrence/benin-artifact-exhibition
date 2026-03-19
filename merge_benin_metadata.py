import pandas as pd

manifest_path = "benin_output/artifact_manifest.csv"
descriptions_path = "benin_descriptions.csv"
output_path = "benin_output/artifact_manifest_enriched.csv"

# Load files
manifest = pd.read_csv(manifest_path)
descriptions = pd.read_csv(descriptions_path)

# Clean key columns
manifest["artifact_id"] = manifest["artifact_id"].astype(str).str.strip().str.lower()
descriptions["artifact_id"] = descriptions["artifact_id"].astype(str).str.strip().str.lower()

# Optional: drop duplicate description rows if any
descriptions = descriptions.drop_duplicates(subset=["artifact_id"], keep="first")

# Merge
merged = manifest.merge(descriptions, on="artifact_id", how="left")

# Add a simple title column from description if useful
def make_title(desc):
    if pd.isna(desc):
        return ""
    # take first sentence or first 90 chars
    first = str(desc).split(".")[0].strip()
    return first[:90]

merged["title"] = merged["description"].apply(make_title)

# Reorder columns if present
preferred_order = [
    "artifact_id",
    "title",
    "description",
    "main_image",
    "detail_image",
    "has_pair",
    "cluster",
]
existing = [c for c in preferred_order if c in merged.columns]
remaining = [c for c in merged.columns if c not in existing]
merged = merged[existing + remaining]

# Save
merged.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Saved: {output_path}")
print(f"Manifest rows: {len(manifest)}")
print(f"Description rows: {len(descriptions)}")
print(f"Matched descriptions: {merged['description'].notna().sum()}")
print(f"Unmatched rows: {merged['description'].isna().sum()}")