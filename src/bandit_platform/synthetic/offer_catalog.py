from __future__ import annotations

from pathlib import Path

import pandas as pd

OFFERS = [
    {
        "offer_id": "cdb_12m",
        "name": "CDB Prazo Fixo 12 meses",
        "channel": "email",
        "product_type": "cdb",
        "description": "Certificado de Deposito Bancario com prazo fixo de 12 meses.",
        "policy_doc": "policy_cdb.md",
    },
    {
        "offer_id": "cdb_24m",
        "name": "CDB Prazo Fixo 24 meses",
        "channel": "call",
        "product_type": "cdb",
        "description": "Certificado de Deposito Bancario com prazo fixo de 24 meses e taxa maior.",
        "policy_doc": "policy_cdb.md",
    },
    {
        "offer_id": "poupanca_programada",
        "name": "Poupanca Programada",
        "channel": "sms",
        "product_type": "poupanca",
        "description": "Poupanca com aporte mensal programado.",
        "policy_doc": "policy_poupanca.md",
    },
    {
        "offer_id": "reserva_emergencia",
        "name": "Consultoria Reserva de Emergencia",
        "channel": "push",
        "product_type": "consultivo",
        "description": "Mensagem consultiva sobre formacao de reserva de emergencia.",
        "policy_doc": "policy_consultivo.md",
    },
    {
        "offer_id": "fundo_liquidez_diaria",
        "name": "Fundo Liquidez Diaria",
        "channel": "email",
        "product_type": "fundo",
        "description": "Fundo de investimento com resgate em D+0.",
        "policy_doc": "policy_fundo.md",
    },
    {
        "offer_id": "taxa_promocional",
        "name": "Aviso de Taxa Promocional",
        "channel": "sms",
        "product_type": "cdb",
        "description": "Aviso de taxa promocional por tempo limitado em CDB.",
        "policy_doc": "policy_cdb.md",
    },
]


def build_offer_catalog() -> pd.DataFrame:
    return pd.DataFrame(OFFERS)


def save_offer_catalog(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
