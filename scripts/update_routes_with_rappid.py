#!/usr/bin/env python3
"""Batch update static *_all_routes.csv files with RAPPID live train data.

Usage:
  python scripts/update_routes_with_rappid.py --csv-dir . --out-dir updated_data --workers 6

This script:
- Scans for files matching `*_all_routes.csv` under `--csv-dir`.
- For each unique train number in CSVs, fetches RAPPID JSON and saves to `data/rappid/<train_no>.json`.
- Produces updated CSV copies named `<orig>_updated.csv` with added columns `rappid_last_updated` and `rappid_data_file`.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests

BASE_URL = "https://rappid.in/apis/train.php"


def fetch_rappid(train_no: str, timeout: int = 10, max_attempts: int = 3) -> dict | None:
    params = {"train_no": train_no}
    attempt = 0
    while attempt < max_attempts:
        try:
            r = requests.get(BASE_URL, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            attempt += 1
            time.sleep(2 ** attempt)
    return None


def find_csv_files(csv_dir: Path) -> list[Path]:
    return list(csv_dir.glob("**/*_all_routes.csv"))


def parse_train_numbers(csv_path: Path) -> list[str]:
    train_nos = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Common field names: Train Number,Train_Number,Train No,TrainNo,Train
        possible_keys = [k for k in reader.fieldnames if re.search(r"train", k, re.I)]
        for row in reader:
            for k in possible_keys:
                val = (row.get(k) or "").strip()
                if val:
                    train_nos.append(re.sub(r"\D", "", val))
                    break
    return [t for t in train_nos if t]


def save_json(out_dir: Path, train_no: str, data: dict):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{train_no}.json"
    data_with_meta = {"fetched_at": datetime.utcnow().isoformat(), "train_no": train_no, "response": data}
    with path.open("w", encoding="utf-8") as f:
        json.dump(data_with_meta, f, ensure_ascii=False, indent=2)
    return path


def update_csv_with_rappid(csv_path: Path, out_csv: Path, rappid_map: dict, rappid_dir: Path):
    with csv_path.open("r", encoding="utf-8") as fr, out_csv.open("w", encoding="utf-8", newline="") as fw:
        reader = csv.DictReader(fr)
        fieldnames = list(reader.fieldnames) + ["rappid_last_updated", "rappid_data_file"]
        writer = csv.DictWriter(fw, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            # find train number again
            possible_keys = [k for k in reader.fieldnames if re.search(r"train", k, re.I)]
            train_no = ""
            for k in possible_keys:
                val = (row.get(k) or "").strip()
                if val:
                    train_no = re.sub(r"\D", "", val)
                    break
            meta = rappid_map.get(train_no)
            if meta:
                row["rappid_last_updated"] = meta.get("fetched_at", "")
                row["rappid_data_file"] = str((rappid_dir / f"{train_no}.json").as_posix())
                # Update train name if present
                train_name = meta.get("response", {}).get("train_name")
                if train_name:
                    # prefer common column names
                    for k in reader.fieldnames:
                        if re.search(r"train.*name", k, re.I):
                            row[k] = train_name
                            break
            else:
                row["rappid_last_updated"] = ""
                row["rappid_data_file"] = ""
            writer.writerow(row)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv-dir", default=".", help="Directory to scan for *_all_routes.csv")
    p.add_argument("--out-dir", default="updated_data", help="Directory to write updated CSVs")
    p.add_argument("--data-dir", default="data/rappid", help="Directory to save raw RAPPID JSON")
    p.add_argument("--workers", type=int, default=5)
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    csv_dir = Path(args.csv_dir)
    out_dir = Path(args.out_dir)
    rappid_dir = Path(args.data_dir)

    csv_files = find_csv_files(csv_dir)
    if not csv_files:
        print("No *_all_routes.csv files found.")
        return

    # collect unique train numbers
    train_set = set()
    csv_to_trains = {}
    for csv_path in csv_files:
        trains = parse_train_numbers(csv_path)
        csv_to_trains[csv_path] = trains
        train_set.update(trains)

    print(f"Found {len(csv_files)} CSV files and {len(train_set)} unique trains to fetch.")

    rappid_map = {}
    if not args.dry_run:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(fetch_rappid, t, args.timeout): t for t in train_set}
            for fut in as_completed(futures):
                t = futures[fut]
                try:
                    resp = fut.result()
                except Exception as e:
                    print(f"Error fetching {t}: {e}")
                    resp = None
                if resp is not None:
                    path = save_json(rappid_dir, t, resp)
                    rappid_map[t] = {"fetched_at": datetime.utcnow().isoformat(), "response": resp, "file": str(path)}

    # produce updated CSVs
    out_dir.mkdir(parents=True, exist_ok=True)
    for csv_path, trains in csv_to_trains.items():
        out_csv = out_dir / (csv_path.stem + "_updated.csv")
        if args.dry_run:
            print(f"Would write updated CSV to {out_csv}")
        else:
            update_csv_with_rappid(csv_path, out_csv, rappid_map, rappid_dir)
            print(f"Wrote {out_csv}")


if __name__ == "__main__":
    main()
