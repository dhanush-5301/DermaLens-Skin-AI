"""
Download HAM10000 dataset from Harvard Dataverse (no login required).
Downloads: metadata CSV + images (Part 1 & Part 2)

Usage: python download_dataset.py
"""

import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

DATA_DIR = Path("data/HAM10000")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Harvard Dataverse file IDs for HAM10000
FILES = {
    "HAM10000_metadata": {
        "url": "https://dataverse.harvard.edu/api/access/datafile/3172585",
        "filename": "HAM10000_metadata.csv",
        "is_zip": False,
    },
    "HAM10000_images_part1": {
        "url": "https://dataverse.harvard.edu/api/access/datafile/3172584",
        "filename": "HAM10000_images_part_1.zip",
        "is_zip": True,
    },
    "HAM10000_images_part2": {
        "url": "https://dataverse.harvard.edu/api/access/datafile/3172582",
        "filename": "HAM10000_images_part_2.zip",
        "is_zip": True,
    },
}


def download_with_progress(url, dest_path):
    """Download a file with progress bar."""
    print(f"  Downloading: {dest_path.name}")

    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            pct = min(100, downloaded * 100 / total_size)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            bar = "=" * int(pct // 2) + ">" + " " * (50 - int(pct // 2))
            sys.stdout.write(f"\r  [{bar}] {pct:.0f}% ({mb_down:.1f}/{mb_total:.1f} MB)")
            sys.stdout.flush()
        else:
            mb_down = downloaded / (1024 * 1024)
            sys.stdout.write(f"\r  Downloaded: {mb_down:.1f} MB")
            sys.stdout.flush()

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
    urllib.request.install_opener(opener)
    urllib.request.urlretrieve(url, str(dest_path), reporthook=progress_hook)
    print()  # newline after progress


def main():
    print("=" * 60)
    print("HAM10000 Dataset Downloader (Harvard Dataverse)")
    print("=" * 60)
    print(f"Target directory: {DATA_DIR.resolve()}\n")

    for name, info in FILES.items():
        dest = DATA_DIR / info["filename"]

        # Skip if already downloaded
        if not info["is_zip"] and dest.exists():
            print(f"OK {info['filename']} already exists, skipping.")
            continue

        # For zips, check if already extracted
        if info["is_zip"]:
            extract_dir = DATA_DIR / name
            if extract_dir.exists() and any(extract_dir.iterdir()):
                print(f"OK {name}/ already extracted, skipping.")
                continue

        print(f"\n-- {name} --")
        download_with_progress(info["url"], dest)

        if info["is_zip"]:
            print(f"  Extracting {info['filename']}...")
            with zipfile.ZipFile(str(dest), "r") as zf:
                zf.extractall(str(DATA_DIR))
            print(f"  OK Extracted to {DATA_DIR}")
            # Clean up zip
            dest.unlink()
            print(f"  OK Removed zip file")

    # Verify
    print("\n" + "=" * 60)
    print("Verifying dataset...")

    csv_path = DATA_DIR / "HAM10000_metadata.csv"
    if csv_path.exists():
        import csv
        with open(csv_path, "r") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = sum(1 for _ in reader)
        print(f"  OK Metadata CSV: {rows} entries")
        print(f"  OK Columns: {header}")
    else:
        print("  FAIL Metadata CSV not found!")

    # Count images
    img_count = 0
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        img_count += len(list(DATA_DIR.rglob(ext)))
    print(f"  OK Total images found: {img_count}")

    if img_count > 0 and csv_path.exists():
        print(f"\nOK Dataset ready! You can now train:")
        print(f"   python train.py --data_dir data/HAM10000 --epochs 30 --batch_size 32")
    else:
        print(f"\nFAIL Dataset incomplete. Please check the downloads.")

    print("=" * 60)


if __name__ == "__main__":
    main()
