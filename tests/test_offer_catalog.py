import pandas as pd

from bandit_platform.synthetic.offer_catalog import (
    OFFERS,
    build_offer_catalog,
    save_offer_catalog,
)


def test_build_offer_catalog_has_unique_offer_ids():
    df = build_offer_catalog()
    assert len(df) == len(OFFERS)
    assert df["offer_id"].is_unique


def test_build_offer_catalog_has_required_columns():
    df = build_offer_catalog()
    assert set(df.columns) == {
        "offer_id", "name", "channel", "product_type", "description", "policy_doc",
    }


def test_build_offer_catalog_channels_are_known():
    df = build_offer_catalog()
    assert set(df["channel"]) <= {"email", "sms", "push", "call"}


def test_save_offer_catalog_writes_csv(tmp_path):
    df = build_offer_catalog()
    out_path = tmp_path / "offer_catalog.csv"

    save_offer_catalog(df, out_path)

    on_disk = pd.read_csv(out_path)
    assert len(on_disk) == len(df)
    assert list(on_disk.columns) == list(df.columns)
