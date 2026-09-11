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


def write_bronze_table(
    df: pd.DataFrame,
    table_name: str,
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Write an immutable Parquet snapshot for a source table."""
    table_dir = (
        BRONZE_DIR
        / table_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
    )

    table_dir.mkdir(parents=True, exist_ok=True)

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


def run_bronze_layer() -> None:
    """Extract source data and persist an immutable Bronze snapshot."""
    batch_id = str(uuid.uuid4())
    ingestion_ts = datetime.now(UTC)
    ingestion_date = ingestion_ts.strftime("%Y-%m-%d")

    logger.info(
        "Starting Bronze layer | batch_id=%s",
        batch_id,
    )

    raw_data = extract_all()

    validate_extracted_data(raw_data)

    logger.info(
        "Extraction completed successfully | tables=%d",
        len(SOURCE_TABLES),
    )

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

    logger.info(
        "Bronze layer completed successfully | batch_id=%s",
        batch_id,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    run_bronze_layer()