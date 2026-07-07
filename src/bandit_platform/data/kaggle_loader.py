from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import dotenv
import pandas as pd

KAGGLE_REF = "henriqueyamahata/bank-marketing"


def load_raw(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path, sep=";")


def _ensure_kaggle_api_token() -> None:
    dotenv.load_dotenv()
    if not os.environ.get("KAGGLE_API_TOKEN"):
        raise RuntimeError(
            "KAGGLE_API_TOKEN not set. Generate a token at "
            "https://www.kaggle.com/settings/api and add it to your local .env "
            "file (see .env.example)."
        )


def download_dataset(dest_dir: str | Path) -> Path:
    _ensure_kaggle_api_token()

    from kaggle.api.kaggle_api_extended import KaggleApi

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(KAGGLE_REF, path=str(dest_dir), unzip=True)

    csv_files = sorted(dest_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV found in {dest_dir} after downloading {KAGGLE_REF}"
        )
    return csv_files[0]


def write_manifest(
    csv_path: str | Path,
    manifest_path: str | Path,
    downloaded_at: str,
) -> dict:
    csv_path = Path(csv_path)
    manifest_path = Path(manifest_path)
    sha256 = hashlib.sha256(csv_path.read_bytes()).hexdigest()

    manifest = {
        "source": "kaggle",
        "kaggle_ref": KAGGLE_REF,
        "sha256": sha256,
        "downloaded_at": downloaded_at,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
