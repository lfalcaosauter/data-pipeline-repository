"""Unit tests for Silver validation functions."""

import pandas as pd
import pytest

from silver.validation import (
    deduplicate_latest,
    split_null_primary_keys,
    validate_required_columns,
)


def test_validate_required_columns_accepts_valid_dataframe():
    """Validate a DataFrame containing all required columns."""
    df = pd.DataFrame(
        {
            "agencia_id": [1],
            "nome_agencia": ["Agencia Central"],
            "cidade": ["Recife"],
        }
    )

    validate_required_columns(df, "agencias")


def test_validate_required_columns_rejects_missing_column():
    """Raise ValueError when a required column is missing."""
    df = pd.DataFrame(
        {
            "agencia_id": [1],
            "nome_agencia": ["Agencia Central"],
        }
    )

    with pytest.raises(ValueError, match="cidade"):
        validate_required_columns(df, "agencias")


def test_split_null_primary_keys_separates_invalid_rows():
    """Separate rows with null primary keys."""
    df = pd.DataFrame(
        {
            "cliente_id": [1, None, 3],
            "nome": ["Ana", "Bruno", "Carlos"],
        }
    )

    valid, invalid = split_null_primary_keys(
        df,
        "cliente_id",
    )

    assert len(valid) == 2
    assert len(invalid) == 1
    assert valid["cliente_id"].notna().all()
    assert invalid["cliente_id"].isna().all()


def test_deduplicate_latest_keeps_latest_record():
    """Keep the latest record for duplicated primary keys."""
    df = pd.DataFrame(
        {
            "cliente_id": [1, 1, 2],
            "nome": ["Ana antiga", "Ana atual", "Carlos"],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-15 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                ]
            ),
        }
    )

    deduplicated, rejected = deduplicate_latest(
        df,
        "cliente_id",
    )

    assert len(deduplicated) == 2
    assert len(rejected) == 1

    ana = deduplicated[
        deduplicated["cliente_id"] == 1
    ].iloc[0]

    assert ana["nome"] == "Ana atual"


def test_deduplicate_latest_rejects_null_primary_keys():
    """Reject rows with null primary keys."""
    df = pd.DataFrame(
        {
            "cliente_id": [1, None],
            "nome": ["Ana", "Sem ID"],
        }
    )

    deduplicated, rejected = deduplicate_latest(
        df,
        "cliente_id",
    )

    assert len(deduplicated) == 1
    assert len(rejected) == 1
    assert rejected["cliente_id"].isna().all()