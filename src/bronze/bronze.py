import logging
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from extraction.extract import SOURCE_TABLES, extract_all

load_dotenv()

logger = logging.getLogger(__name__)


PROJECT_DIR = Path(__file__).resolve().parents[2]

BRONZE_DIR = Path(
    os.getenv(
        "BRONZE_DIR",
        str(PROJECT_DIR / "data" / "bronze"),
    )
)

SOURCE_SYSTEM = "banking_oltp_postgres"


def add_audit_columns(
    df: pd.DataFrame,
    batch_id: str,
    ingestion_ts: datetime,
) -> pd.DataFrame:
    """Add technical audit columns without changing business data."""
    result = df.copy()

    result["_source_system"] = SOURCE_SYSTEM
    result["_ingestion_timestamp"] = ingestion_ts
    result["_batch_id"] = batch_id

    return result


def validate_extracted_data(
    raw_data: dict[str, pd.DataFrame],
) -> None:
    """Validate the structure returned by the extraction layer."""
    missing_tables = [
        table_name
        for table_name in SOURCE_TABLES
        if table_name not in raw_data
    ]

    if missing_tables:
        raise ValueError(
            "Extraction did not return all expected tables: "
            f"{', '.join(missing_tables)}"
        )

    invalid_tables = [
        table_name
        for table_name in SOURCE_TABLES
        if not isinstance(raw_data[table_name], pd.DataFrame)
    ]

    if invalid_tables:
        raise TypeError(
            "Extraction returned invalid data for table(s): "
            f"{', '.join(invalid_tables)}"
        )


def get_batch_table_dir(
    table_name: str,
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Return the directory for one Bronze table batch."""
    return (
        BRONZE_DIR
        / table_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
    )


def write_bronze_table(
    df: pd.DataFrame,
    table_name: str,
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Write one immutable Bronze Parquet snapshot."""
    table_dir = get_batch_table_dir(
        table_name=table_name,
        ingestion_date=ingestion_date,
        batch_id=batch_id,
    )

    table_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = table_dir / f"{table_name}.parquet"

    df.to_parquet(
        file_path,
        index=False,
        engine="pyarrow",
    )

    logger.info(
        "Bronze table '%s' written | rows=%d | path=%s",
        table_name,
        len(df),
        file_path,
    )

    return file_path


def write_success_marker(
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """
    Write a success marker after all Bronze tables are persisted.

    The marker indicates that the batch completed successfully.
    """
    marker_dir = (
        BRONZE_DIR
        / "_metadata"
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
    )

    marker_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    marker_path = marker_dir / "_SUCCESS"

    marker_path.write_text(
        "Bronze batch completed successfully.\n",
        encoding="utf-8",
    )

    logger.info(
        "Bronze success marker written | batch_id=%s | path=%s",
        batch_id,
        marker_path,
    )

    return marker_path


def run_bronze_layer() -> None:
    """Extract source data and persist an immutable Bronze snapshot."""
    batch_id = str(uuid.uuid4())
    ingestion_ts = datetime.now(UTC)
    ingestion_date = ingestion_ts.strftime("%Y-%m-%d")

    logger.info(
        "Starting Bronze layer | batch_id=%s | ingestion_date=%s",
        batch_id,
        ingestion_date,
    )

    try:
        raw_data = extract_all()

        validate_extracted_data(raw_data)

        logger.info(
            "Extraction completed successfully | tables=%d",
            len(SOURCE_TABLES),
        )

        written_tables = 0

        for table_name in SOURCE_TABLES:
            df = raw_data[table_name]

            bronze_df = add_audit_columns(
                df=df,
                batch_id=batch_id,
                ingestion_ts=ingestion_ts,
            )

            write_bronze_table(
                df=bronze_df,
                table_name=table_name,
                ingestion_date=ingestion_date,
                batch_id=batch_id,
            )

            written_tables += 1

        if written_tables != len(SOURCE_TABLES):
            raise RuntimeError(
                "Bronze batch did not write all expected tables. "
                f"Expected={len(SOURCE_TABLES)} "
                f"Written={written_tables}"
            )

        write_success_marker(
            ingestion_date=ingestion_date,
            batch_id=batch_id,
        )

        logger.info(
            "Bronze layer completed successfully | "
            "batch_id=%s | tables=%d",
            batch_id,
            written_tables,
        )

    except Exception:
        logger.exception(
            "Bronze layer failed | batch_id=%s",
            batch_id,
        )
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    run_bronze_layer()