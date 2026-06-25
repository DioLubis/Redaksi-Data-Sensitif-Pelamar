from __future__ import annotations

import argparse
import importlib
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


SOURCES = {
    "wider_face": {
        "url": "https://shuoyang1213.me/WIDERFACE/",
        "note": "Download image zips and wider_face_split from the official page or use torchvision.datasets.WIDERFace.",
    },
    "doclaynet": {
        "url": "https://huggingface.co/datasets/docling-project/DocLayNet",
        "note": "Use Hugging Face datasets. This is large; prefer streaming or a selected subset for prototype.",
    },
    "funsd": {
        "url": "https://guillaumejaume.github.io/FUNSD/",
        "direct_zip": "https://guillaumejaume.github.io/FUNSD/dataset.zip",
        "note": "Small official dataset for scanned forms and OCR/layout validation.",
    },
    "midv500": {
        "url": "https://github.com/fcakyon/midv500",
        "note": "Use the midv500 tooling or official FTP/source referenced by the project.",
    },
}


def run(command: list[str]) -> None:
    print(" ".join(command))
    subprocess.run(command, check=True)


def download_doclaynet(output_dir: Path, split: str, limit: int | None) -> None:
    try:
        cwd = str(Path.cwd())
        original_path = list(sys.path)
        sys.path = [p for p in sys.path if p not in ("", cwd)]
        hf_datasets = importlib.import_module("datasets")
        sys.path = original_path
        load_dataset = hf_datasets.load_dataset
    except ImportError as exc:
        raise SystemExit("Install dependency first: pip install datasets") from exc
    except AttributeError as exc:
        raise SystemExit(
            "The Hugging Face 'datasets' package was not found. "
            "Install with: pip install datasets"
        ) from exc
    finally:
        if "original_path" in locals():
            sys.path = original_path

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset = load_dataset("docling-project/DocLayNet", split=split, streaming=limit is not None)
    if limit is not None:
        dataset = dataset.take(limit)

    for index, item in enumerate(dataset):
        image = item.get("image")
        if image is None:
            continue
        image_path = output_dir / f"doclaynet_{split}_{index:06d}.png"
        image.save(image_path)
        if limit is not None and index + 1 >= limit:
            break


def download_funsd(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "funsd.zip"
    extracted_marker = output_dir / ".download_complete"
    if extracted_marker.exists():
        print(f"FUNSD already downloaded at {output_dir}")
        return

    url = SOURCES["funsd"]["direct_zip"]
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, zip_path)
    print(f"Extracting {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(output_dir)
    extracted_marker.write_text("ok\n", encoding="utf-8")
    print(f"Saved FUNSD to {output_dir}")


def print_instructions(dataset: str) -> None:
    source = SOURCES[dataset]
    print(f"{dataset}: {source['url']}")
    print(source["note"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset downloader helper.")
    parser.add_argument("--dataset", choices=sorted(SOURCES), required=True)
    parser.add_argument("--output", default="datasets/raw", type=Path)
    parser.add_argument("--split", default="train")
    parser.add_argument("--limit", type=int, help="Optional prototype subset limit.")
    parser.add_argument("--instructions-only", action="store_true")
    args = parser.parse_args()

    if args.instructions_only:
        print_instructions(args.dataset)
        return

    target = args.output / args.dataset
    if args.dataset == "doclaynet":
        download_doclaynet(target, args.split, args.limit)
        print(f"Saved DocLayNet subset to {target}")
        return
    if args.dataset == "funsd":
        download_funsd(target)
        return

    print_instructions(args.dataset)
    print("This source requires manual/license-aware download or a source-specific tool.")
    print(f"Place extracted files under: {target}")


if __name__ == "__main__":
    main()
