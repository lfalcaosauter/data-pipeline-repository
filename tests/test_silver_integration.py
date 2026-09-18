from silver.config import SILVER_DIR, SOURCE_TABLES
from silver.io import find_latest_complete_batch
from silver.silver import run_silver_layer


def test_silver_creates_complete_batch():
    """Silver should create all expected tables and a success marker."""
    batch_id, ingestion_date = find_latest_complete_batch()

    run_silver_layer()

    for table_name in SOURCE_TABLES:
        table_file = (
            SILVER_DIR
            / table_name
            / f"ingestion_date={ingestion_date}"
            / f"batch_id={batch_id}"
            / f"{table_name}.parquet"
        )

        assert table_file.exists(), (
            f"Silver table was not created: {table_file}"
        )

    success_marker = (
        SILVER_DIR
        / "_metadata"
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
        / "_SUCCESS"
    )

    assert success_marker.exists()


def test_silver_reprocessing_does_not_create_duplicate_batch():
    """Reprocessing the same batch should reuse its existing path."""
    batch_id, ingestion_date = find_latest_complete_batch()

    run_silver_layer()
    run_silver_layer()

    for table_name in SOURCE_TABLES:
        table_dir = (
            SILVER_DIR
            / table_name
            / f"ingestion_date={ingestion_date}"
            / f"batch_id={batch_id}"
        )

        files = list(table_dir.glob(f"{table_name}.parquet"))

        assert len(files) == 1, (
            f"Expected exactly one Silver file for '{table_name}', "
            f"found {len(files)}."
        )

        assert files[0].exists()