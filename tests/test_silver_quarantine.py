
import pandas as pd

from silver.io import quarantine


def test_quarantine_writes_rejected_rows(tmp_path, monkeypatch):
    """Quarantine should persist rejected rows as a Parquet file."""
    import silver.io

    monkeypatch.setattr(silver.io, "REJECTS_DIR", tmp_path)

    df = pd.DataFrame(
        {
            "cliente_id": [1, 2],
            "nome": ["Cliente válido", "Cliente inválido"],
            "cpf": ["12345678901", None],
        }
    )

    quarantine(
        df=df,
        table_name="clientes",
        reason="Required field is null.",
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    rejected_file = (
        tmp_path
        / "clientes"
        / "ingestion_date=2026-09-16"
        / "batch_id=test-batch"
        / "rejected.parquet"
    )

    assert rejected_file.exists()

    rejected = pd.read_parquet(rejected_file)

    assert len(rejected) == 2
    assert "_reject_reason" in rejected.columns
    assert "_rejected_at" in rejected.columns
    assert rejected["_reject_reason"].iloc[0] == "Required field is null."

def test_process_clientes_quarantines_invalid_rows(tmp_path, monkeypatch):
    """Invalid client rows should be written to quarantine."""
    import silver.io

    monkeypatch.setattr(silver.io, "REJECTS_DIR", tmp_path)

    df = pd.DataFrame(
        {
            "cliente_id": [1, None],
            "nome": ["Cliente válido", "Cliente inválido"],
            "cpf": ["12345678901", "12345678902"],
            "data_nascimento": pd.to_datetime(
                ["1990-01-01", "1995-01-01"]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    from silver.transformations import process_clientes

    result = process_clientes(
        df,
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["cliente_id"] == 1

    rejected_file = (
        tmp_path
        / "clientes"
        / "ingestion_date=2026-09-16"
        / "batch_id=test-batch"
        / "rejected.parquet"
    )

    assert rejected_file.exists()

    rejected = pd.read_parquet(rejected_file)

    assert len(rejected) == 1
    assert pd.isna(rejected.iloc[0]["cliente_id"])