from pathlib import Path

from bandit_platform.synthetic.offer_catalog import build_offer_catalog

POLICY_DIR = Path(__file__).parent.parent / "data" / "synthetic_enrichment" / "policy_docs"


def test_every_offer_policy_doc_exists():
    catalog = build_offer_catalog()
    for policy_doc in catalog["policy_doc"].unique():
        assert (POLICY_DIR / policy_doc).exists(), f"missing {policy_doc}"


def test_suitability_geral_doc_exists_and_is_not_empty():
    doc = POLICY_DIR / "suitability_geral.md"
    assert doc.exists()
    assert len(doc.read_text()) > 100
