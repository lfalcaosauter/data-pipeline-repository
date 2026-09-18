import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from silver.config import (
    BRONZE_DIR,
    PARQUET_PATTERN,
    REJECTS_DIR,
    SILVER_DIR,
    SOURCE_TABLES,
)

logger = logging.getLogger(__name__)


def get_batch_ids(table_name: str) -> set[str]:
    """Return all Bronze batch IDs available for a table."""
    table_dir = BRONZE_DIR / table_name

    if not table_dir.exists():
        return set()

    batch_ids: set[str] = set()

    for parquet_file in table_dir.rglob(PARQUET_PATTERN):
        relative_parts = parquet_file.relative_to(table_dir).parts

        for part in relative_parts:
            if part.startswith("batch_id="):
                batch_ids.add(part.split("=", 1)[1])

    return batch_ids


def get_common_batch_ids() -> set[str]:
    """Return batch IDs available for every source table."""
    batch_sets = [
        get_batch_ids(table_name)
        for table_name in SOURCE_TABLES
    ]

    if not batch_sets:
        return set()

    return set.intersection(*batch_sets)


def get_batch_ingestion_timestamp(
    table_name: str,
    batch_id: str,
) -> datetime:
    """Read the ingestion timestamp from a Bronze batch."""
    table_dir = BRONZE_DIR / table_name

    batch_files = list(
        table_dir.rglob(
            f"batch_id={batch_id}/{table_name}.parquet"
        )
    )

    if not batch_files:
        raise FileNotFoundError(
            f"Bronze batch not found | table={table_name} | "
            f"batch_id={batch_id}"
        )

    df = pd.read_parquet(batch_files[0])

    if "_ingestion_timestamp" not in df.columns:
        raise ValueError(
            f"Missing _ingestion_timestamp | table={table_name} | "
            f"batch_id={batch_id}"
        )

    timestamp = pd.to_datetime(
        df["_ingestion_timestamp"],
        utc=True,
    ).iloc[0]

    return timestamp.to_pydatetime()


def find_latest_complete_batch() -> tuple[str, str]:
    """Find the most recent Bronze batch available for every table."""
    common_batches = get_common_batch_ids()

    if not common_batches:
        raise RuntimeError(
            "No complete Bronze batch found for all source tables."
        )

    batch_metadata: list[tuple[str, datetime]] = []

    for batch_id in common_batches:
        timestamp = get_batch_ingestion_timestamp(
            SOURCE_TABLES[0],
            batch_id,
        )

        batch_metadata.append(
            (batch_id, timestamp)
        )

    batch_id, ingestion_timestamp = max(
        batch_metadata,
        key=lambda item: item[1],
    )

    ingestion_date = ingestion_timestamp.date().isoformat()

    logger.info(
        "Latest complete Bronze batch selected | "
        "batch_id=%s | ingestion_date=%s | available_batches=%d",
        batch_id,
        ingestion_date,
        len(common_batches),
    )

    return batch_id, ingestion_date


def read_bronze_table(
    table_name: str,
    batch_id: str,
) -> pd.DataFrame:
    """Read one Bronze table for a specific batch."""
    table_dir = BRONZE_DIR / table_name

    batch_files = list(
        table_dir.rglob(
            f"batch_id={batch_id}/{table_name}.parquet"
        )
    )

    if not batch_files:
        raise FileNotFoundError(
            f"Bronze data not found | table={table_name} | "
            f"batch_id={batch_id}"
        )

    if len(batch_files) > 1:
        raise RuntimeError(
            f"Multiple Bronze files found | table={table_name} | "
            f"batch_id={batch_id}"
        )

    df = pd.read_parquet(batch_files[0])

    logger.info(
        "Bronze table read | table=%s | batch_id=%s | rows=%d",
        table_name,
        batch_id,
        len(df),
    )

    return df


def quarantine(
    df: pd.DataFrame,
    table_name: str,
    reason: str,
    batch_id: str,
    ingestion_date: str,
) -> None:
    """Write rejected records to a batch-specific quarantine area."""
    if df.empty:
        return

    rejected = df.copy()

    rejected["_reject_reason"] = reason
    rejected["_rejected_at"] = pd.Timestamp.now(tz="UTC")

    reject_dir = (
        REJECTS_DIR
        / table_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
    )

    reject_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = reject_dir / "rejected.parquet"

    rejected.to_parquet(
        file_path,
        index=False,
        engine="pyarrow",
    )

    logger.warning(
        "Quarantined %d row(s) from '%s': %s.",
        len(rejected),
        table_name,
        reason,
    )


def get_silver_batch_dir(
    table_name: str,
    batch_id: str,
    ingestion_date: str,
) -> Path:
    """Return the directory for a specific Silver batch."""
    return (
        SILVER_DIR
        / table_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
    )


def get_silver_success_marker(
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Return the Silver success marker path."""
    return (
        SILVER_DIR
        / "_metadata"
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
        / "_SUCCESS"
    )


def write_silver_table(
    df: pd.DataFrame,
    table_name: str,
    batch_id: str,
    ingestion_date: str,
) -> None:
    """Write one Silver table using ingestion_date as partition."""
    table_dir = get_silver_batch_dir(
        table_name=table_name,
        batch_id=batch_id,
        ingestion_date=ingestion_date,
    )

    table_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = table_dir / f"{table_name}.parquet"

    df.to_parquet(
        output_file,
        index=False,
        engine="pyarrow",
    )

    logger.info(
        "Silver table written | table=%s | rows=%d | "
        "partition=ingestion_date=%s | batch_id=%s | path=%s",
        table_name,
        len(df),
        ingestion_date,
        batch_id,
        output_file,
    )


def write_success_marker(
    ingestion_date: str,
    batch_id: str,
) -> None:
    """Write a success marker after the complete Silver batch."""
    marker = get_silver_success_marker(
        ingestion_date=ingestion_date,
        batch_id=batch_id,
    )

    marker.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    marker.touch()

    logger.info(
        "Silver success marker written | batch_id=%s | path=%s",
        batch_id,
        marker,
    )