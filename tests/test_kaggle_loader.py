import hashlib
import json
from pathlib import Path

import dotenv
import pandas as pd
import pytest

from bandit_platform.data.kaggle_loader import (
    _ensure_kaggle_api_token,
    load_raw,
    write_manifest,
)

FIXTURE = Path(__file__).parent / "fixtures" / "bank_marketing_sample.csv"


def test_load_raw_parses_semicolon_delimited_csv():
    df = load_raw(FIXTURE)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 8
    assert list(df.columns) == [
        "age", "job", "marital", "education", "default", "balance",
        "housing", "loan", "contact", "day", "month", "duration",
        "campaign", "pdays", "previous", "poutcome", "y",
    ]
    assert df["age"].dtype.kind == "i"
    assert set(df["y"].unique()) <= {"yes", "no"}


def test_write_manifest_records_sha256_and_source(tmp_path):
    manifest_path = tmp_path / "dataset_manifest.json"
    expected_sha256 = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()

    result = write_manifest(
        FIXTURE,
        manifest_path,
        downloaded_at="2026-07-07T00:00:00Z",
    )

    assert result["sha256"] == expected_sha256
    assert result["source"] == "kaggle"
    assert result["kaggle_ref"] == "henriqueyamahata/bank-marketing"
    assert result["downloaded_at"] == "2026-07-07T00:00:00Z"

    on_disk = json.loads(manifest_path.read_text())
    assert on_disk == result


def test_ensure_kaggle_api_token_raises_when_missing(monkeypatch):
    monkeypatch.delenv("KAGGLE_API_TOKEN", raising=False)
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="KAGGLE_API_TOKEN"):
        _ensure_kaggle_api_token()


def test_ensure_kaggle_api_token_passes_when_set(monkeypatch):
    monkeypatch.setenv("KAGGLE_API_TOKEN", "fake-token-for-test")
    _ensure_kaggle_api_token()
