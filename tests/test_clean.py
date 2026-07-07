from pathlib import Path

import pandas as pd

from bandit_platform.data.clean import (
    LEAKAGE_COLUMNS,
    build_processed_dataset,
    drop_leakage_columns,
    save_processed,
)
from bandit_platform.data.kaggle_loader import load_raw

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def test_leakage_columns_includes_duration():
    assert "duration" in LEAKAGE_COLUMNS


def test_drop_leakage_columns_removes_duration_only():
    df = load_raw(FIXTURE)
    cleaned = drop_leakage_columns(df)
    assert "duration" not in cleaned.columns
    assert "pdays" in cleaned.columns
    assert len(cleaned) == len(df)


def test_build_processed_dataset_maps_target_to_binary():
    df = load_raw(FIXTURE)
    processed = build_processed_dataset(df)
    assert "duration" not in processed.columns
    assert set(processed["target"].unique()) <= {0, 1}
    assert (processed["target"] == (processed["y"] == "yes").astype(int)).all()


def test_save_processed_writes_csv(tmp_path):
    df = load_raw(FIXTURE)
    processed = build_processed_dataset(df)
    out_path = tmp_path / "bank_marketing.csv"

    save_processed(processed, out_path)

    on_disk = pd.read_csv(out_path)
    assert len(on_disk) == len(processed)
    assert "duration" not in on_disk.columns
