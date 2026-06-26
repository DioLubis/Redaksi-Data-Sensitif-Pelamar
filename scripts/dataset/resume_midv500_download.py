from __future__ import annotations

import argparse
import os
import urllib.request
import zipfile
from pathlib import Path


MIDV500_LINKS = [
    "ftp://smartengines.com/midv-500/dataset/01_alb_id.zip",
    "ftp://smartengines.com/midv-500/dataset/02_aut_drvlic_new.zip",
    "ftp://smartengines.com/midv-500/dataset/03_aut_id_old.zip",
    "ftp://smartengines.com/midv-500/dataset/04_aut_id.zip",
    "ftp://smartengines.com/midv-500/dataset/05_aze_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/06_bra_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/07_chl_id.zip",
    "ftp://smartengines.com/midv-500/dataset/08_chn_homereturn.zip",
    "ftp://smartengines.com/midv-500/dataset/09_chn_id.zip",
    "ftp://smartengines.com/midv-500/dataset/10_cze_id.zip",
    "ftp://smartengines.com/midv-500/dataset/11_cze_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/12_deu_drvlic_new.zip",
    "ftp://smartengines.com/midv-500/dataset/13_deu_drvlic_old.zip",
    "ftp://smartengines.com/midv-500/dataset/14_deu_id_new.zip",
    "ftp://smartengines.com/midv-500/dataset/15_deu_id_old.zip",
    "ftp://smartengines.com/midv-500/dataset/16_deu_passport_new.zip",
    "ftp://smartengines.com/midv-500/dataset/17_deu_passport_old.zip",
    "ftp://smartengines.com/midv-500/dataset/18_dza_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/19_esp_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/20_esp_id_new.zip",
    "ftp://smartengines.com/midv-500/dataset/21_esp_id_old.zip",
    "ftp://smartengines.com/midv-500/dataset/22_est_id.zip",
    "ftp://smartengines.com/midv-500/dataset/23_fin_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/24_fin_id.zip",
    "ftp://smartengines.com/midv-500/dataset/25_grc_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/26_hrv_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/27_hrv_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/28_hun_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/29_irn_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/30_ita_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/31_jpn_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/32_lva_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/33_mac_id.zip",
    "ftp://smartengines.com/midv-500/dataset/34_mda_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/35_nor_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/36_pol_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/37_prt_id.zip",
    "ftp://smartengines.com/midv-500/dataset/38_rou_drvlic.zip",
    "ftp://smartengines.com/midv-500/dataset/39_rus_internalpassport.zip",
    "ftp://smartengines.com/midv-500/dataset/40_srb_id.zip",
    "ftp://smartengines.com/midv-500/dataset/41_srb_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/42_svk_id.zip",
    "ftp://smartengines.com/midv-500/dataset/43_tur_id.zip",
    "ftp://smartengines.com/midv-500/dataset/44_ukr_id.zip",
    "ftp://smartengines.com/midv-500/dataset/45_ukr_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/46_ury_passport.zip",
    "ftp://smartengines.com/midv-500/dataset/47_usa_bordercrossing.zip",
    "ftp://smartengines.com/midv-500/dataset/48_usa_passportcard.zip",
    "ftp://smartengines.com/midv-500/dataset/49_usa_ssn82.zip",
    "ftp://smartengines.com/midv-500/dataset/50_xpo_id.zip",
]


def document_name_from_url(url: str) -> str:
    return Path(url).stem


def is_complete_document_dir(document_dir: Path) -> bool:
    if not document_dir.is_dir():
        return False
    images_dir = document_dir / "images"
    gt_dir = document_dir / "ground_truth"
    if not images_dir.is_dir() or not gt_dir.is_dir():
        return False
    image_count = sum(1 for p in images_dir.rglob("*") if p.suffix.lower() in {".tif", ".tiff", ".jpg", ".png"})
    gt_count = sum(1 for p in gt_dir.rglob("*.json"))
    return image_count > 0 and gt_count > 0


def download_file(url: str, destination: Path) -> None:
    part_path = destination.with_suffix(destination.suffix + ".part")
    if part_path.exists():
        part_path.unlink()
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, part_path)
    part_path.replace(destination)


def extract_zip(zip_path: Path, output_dir: Path) -> None:
    print(f"Extracting {zip_path.name}")
    with zipfile.ZipFile(zip_path, "r") as archive:
        archive.extractall(output_dir)


def resume_midv500(output_dir: Path, keep_zip: bool, dry_run: bool) -> None:
    dataset_dir = output_dir / "midv500"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    skipped = []
    pending = []
    for url in MIDV500_LINKS:
        name = document_name_from_url(url)
        document_dir = dataset_dir / name
        if is_complete_document_dir(document_dir):
            skipped.append(name)
        else:
            pending.append((url, name))

    print(f"Complete folders skipped: {len(skipped)}")
    if skipped:
        print("Last skipped:", skipped[-1])
    print(f"Pending folders: {len(pending)}")
    if dry_run:
        for _, name in pending:
            print(f"pending: {name}")
        return

    for url, name in pending:
        zip_path = dataset_dir / f"{name}.zip"
        document_dir = dataset_dir / name
        if zip_path.exists():
            try:
                extract_zip(zip_path, dataset_dir)
            except zipfile.BadZipFile:
                print(f"Bad zip found, deleting and re-downloading: {zip_path}")
                zip_path.unlink()
            else:
                if is_complete_document_dir(document_dir):
                    if not keep_zip:
                        zip_path.unlink()
                    continue

        download_file(url, zip_path)
        extract_zip(zip_path, dataset_dir)
        if not is_complete_document_dir(document_dir):
            raise SystemExit(f"Downloaded but folder still looks incomplete: {document_dir}")
        if not keep_zip:
            zip_path.unlink()
        print(f"Done: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume MIDV-500 download without duplicating completed folders.")
    parser.add_argument("--output", default="datasets/raw/midv500_full", type=Path)
    parser.add_argument("--keep-zip", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    resume_midv500(args.output, args.keep_zip, args.dry_run)


if __name__ == "__main__":
    main()

