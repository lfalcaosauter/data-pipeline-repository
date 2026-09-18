import pandas as pd

from silver.config import REQUIRED_COLUMNS


def validate_required_columns(
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """Validate that all expected source columns are present."""
    expected = set(REQUIRED_COLUMNS[table_name])
    available = set(df.columns)

    missing = expected - available

    if missing:
        missing_columns = ", ".join(
            sorted(missing),
        )

        raise ValueError(
            f"Table '{table_name}' is missing required columns: "
            f"{missing_columns}"
        )


def split_null_primary_keys(
    df: pd.DataFrame,
    primary_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate rows with valid and null primary keys."""
    invalid = df[
        df[primary_key].isna()
    ].copy()

    valid = df[
        df[primary_key].notna()
    ].copy()

    return valid, invalid


def deduplicate_latest(
    df: pd.DataFrame,
    primary_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep the latest Bronze version of each primary key."""
    valid, invalid = split_null_primary_keys(
        df,
        primary_key,
    )

    if "_ingestion_timestamp" in valid.columns:
        valid = valid.sort_values(
            "_ingestion_timestamp",
            kind="stable",
        )

    duplicated = valid[
        valid.duplicated(
            subset=[primary_key],
            keep="last",
        )
    ].copy()

    deduplicated = valid.drop_duplicates(
        subset=[primary_key],
        keep="last",
    ).copy()

    rejected = pd.concat(
        [invalid, duplicated],
        ignore_index=True,
    )

    return deduplicated, rejected