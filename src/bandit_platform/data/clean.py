from __future__ import annotations

from pathlib import Path

import pandas as pd

LEAKAGE_COLUMNS = ["duration"]


def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=LEAKAGE_COLUMNS)


def build_processed_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = drop_leakage_columns(df)
    cleaned = cleaned.copy()
    cleaned["target"] = (cleaned["y"] == "yes").astype(int)
    return cleaned


def save_processed(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
