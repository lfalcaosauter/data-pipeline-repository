import logging
import os
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parents[2]

BRONZE_DIR = Path(
    os.getenv(
        "BRONZE_DIR",
        str(PROJECT_DIR / "data" / "bronze"),
    )
)

SILVER_DIR = Path(
    os.getenv(
        "SILVER_DIR",
        str(PROJECT_DIR / "data" / "silver"),
    )
)

REJECTS_DIR = PROJECT_DIR / "data" / "silver_rejects"

SOURCE_TIMEZONE = os.getenv(
    "TIMEZONE",
    "America/Sao_Paulo",
)

SOURCE_TABLES = (
    "agencias",
    "clientes",
    "tipos_transacao",
    "contas",
    "cartoes",
    "emprestimos",
    "transacoes",
)

PARQUET_PATTERN = "*.parquet"

REJECT_NULL_OR_DUPLICATED_PK = (
    "Null or duplicated primary key."
)

REJECT_REQUIRED_FIELD_NULL = (
    "Required field is null."
)

PRIMARY_KEYS = {
    "agencias": "agencia_id",
    "clientes": "cliente_id",
    "tipos_transacao": "tipo_transacao_id",
    "contas": "conta_id",
    "cartoes": "cartao_id",
    "emprestimos": "emprestimo_id",
    "transacoes": "transacao_id",
}

REQUIRED_COLUMNS = {
    "agencias": (
        "agencia_id",
        "nome_agencia",
        "cidade",
    ),
    "clientes": (
        "cliente_id",
        "nome",
        "cpf",
        "data_nascimento",
    ),
    "tipos_transacao": (
        "tipo_transacao_id",
        "descricao",
    ),
    "contas": (
        "conta_id",
        "cliente_id",
        "agencia_id",
        "saldo",
    ),
    "cartoes": (
        "cartao_id",
        "conta_id",
        "numero_cartao",
        "tipo_cartao",
    ),
    "emprestimos": (
        "emprestimo_id",
        "cliente_id",
        "valor_contratado",
        "parcelas",
        "data_contrato",
    ),
    "transacoes": (
        "transacao_id",
        "conta_origem_id",
        "conta_destino_id",
        "tipo_transacao_id",
        "valor",
        "data_hora",
    ),
}


def get_batch_ids(table_name: str) -> set[str]:
    """Return all Bronze batch IDs available for a table."""
    table_dir = BRONZE_DIR / table_name

    if not table_dir.exists():
        raise FileNotFoundError(
            f"Bronze table directory not found: {table_dir}"
        )

    batch_ids: set[str] = set()

    for file_path in table_dir.rglob(PARQUET_PATTERN): 
        for part in file_path.parts:
            if part.startswith("batch_id="):
                batch_id = part.removeprefix("batch_id=")

                if batch_id:
                    batch_ids.add(batch_id)

                break

    return batch_ids


def get_common_batch_ids() -> set[str]:
    """Return batch IDs available for every source table."""
    common_batch_ids: set[str] | None = None

    for table_name in SOURCE_TABLES:
        table_batch_ids = get_batch_ids(table_name)

        if common_batch_ids is None:
            common_batch_ids = table_batch_ids
        else:
            common_batch_ids &= table_batch_ids

    return common_batch_ids or set()


def get_batch_ingestion_timestamp(
    table_name: str,
    batch_id: str,
) -> pd.Timestamp:
    """Read the ingestion timestamp for a Bronze batch."""
    table_dir = BRONZE_DIR / table_name

    files = sorted(
        file_path
        for file_path in table_dir.rglob(PARQUET_PATTERN)
        if f"batch_id={batch_id}" in file_path.parts
    )

    if not files:
        raise FileNotFoundError(
            f"No Bronze files found for table "
            f"'{table_name}' and batch '{batch_id}'."
        )

    metadata = pd.read_parquet(
        files[0],
        columns=["_ingestion_timestamp"],
    )

    if metadata.empty:
        raise ValueError(
            f"Bronze batch '{batch_id}' for table "
            f"'{table_name}' contains no rows."
        )

    timestamp = pd.to_datetime(
        metadata["_ingestion_timestamp"].iloc[0],
        errors="coerce",
        utc=True,
    )

    if pd.isna(timestamp):
        raise ValueError(
            f"Invalid '_ingestion_timestamp' for batch "
            f"'{batch_id}'."
        )

    return timestamp


def find_latest_complete_batch() -> tuple[str, str]:
    """
    Find the newest batch available for every source table.

    A batch is considered complete only when the same batch ID
    exists for all seven source tables.
    """
    common_batch_ids = get_common_batch_ids()

    if not common_batch_ids:
        raise FileNotFoundError(
            "No complete Bronze batch was found across all source tables."
        )

    batch_timestamps: dict[str, pd.Timestamp] = {}

    reference_table = SOURCE_TABLES[0]

    for batch_id in common_batch_ids:
        batch_timestamps[batch_id] = get_batch_ingestion_timestamp(
            reference_table,
            batch_id,
        )

    latest_batch_id = max(
        batch_timestamps,
        key=batch_timestamps.__getitem__,
    )

    latest_timestamp = batch_timestamps[latest_batch_id]
    ingestion_date = latest_timestamp.strftime("%Y-%m-%d")

    logger.info(
        "Latest complete Bronze batch selected | "
        "batch_id=%s | ingestion_date=%s | available_batches=%d",
        latest_batch_id,
        ingestion_date,
        len(common_batch_ids),
    )

    return latest_batch_id, ingestion_date


def read_bronze_table(
    table_name: str,
    batch_id: str,
) -> pd.DataFrame:
    """Read Bronze Parquet files for a specific batch."""
    table_dir = BRONZE_DIR / table_name

    if not table_dir.exists():
        raise FileNotFoundError(
            f"Bronze table directory not found: {table_dir}"
        )

    files = sorted(
        file_path
        for file_path in table_dir.rglob(PARQUET_PATTERN)
        if f"batch_id={batch_id}" in file_path.parts
    )

    if not files:
        raise FileNotFoundError(
            f"No Bronze Parquet files found for table "
            f"'{table_name}' and batch '{batch_id}'."
        )

    frames = [
        pd.read_parquet(file_path)
        for file_path in files
    ]

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    logger.info(
        "Read Bronze table '%s': %d row(s) from %d file(s) | "
        "batch_id=%s.",
        table_name,
        len(result),
        len(files),
        batch_id,
    )

    return result


def quarantine(
    df: pd.DataFrame,
    table_name: str,
    reason: str,
    batch_id: str,
    ingestion_date: str,
) -> None:
    """Persist rejected records for data quality investigation."""
    if df.empty:
        return

    rejected = df.copy()
    rejected["_reject_reason"] = reason
    rejected["_rejected_at"] = datetime.now(UTC)

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


def validate_required_columns(
    df: pd.DataFrame,
    table_name: str,
) -> None:
    """Validate that all expected source columns are present."""
    expected = set(REQUIRED_COLUMNS[table_name])
    available = set(df.columns)

    missing = expected - available

    if missing:
        missing_columns = ", ".join(sorted(missing))

        raise ValueError(
            f"Table '{table_name}' is missing required columns: "
            f"{missing_columns}"
        )


def split_null_primary_keys(
    df: pd.DataFrame,
    primary_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate rows with valid and null primary keys."""
    invalid = df[df[primary_key].isna()].copy()
    valid = df[df[primary_key].notna()].copy()

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


def clean_text_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Remove surrounding and repeated whitespace."""
    result = df.copy()

    text_columns = result.select_dtypes(
        include=["object", "string"],
    ).columns

    for column in text_columns:
        result[column] = (
            result[column]
            .astype("string")
            .str.strip()
            .str.replace(
                r"\s+",
                " ",
                regex=True,
            )
        )

    return result


def normalize_cpf(
    value: Any,
) -> str | None:
    """Normalize a CPF without inventing missing digits."""
    if pd.isna(value):
        return None

    digits = re.sub(
        r"\D",
        "",
        str(value),
    )

    if len(digits) != 11:
        return None

    return digits


def normalize_card_number(
    value: Any,
) -> str | None:
    """Normalize a card number and reject invalid values."""
    if pd.isna(value):
        return None

    digits = re.sub(
        r"\D",
        "",
        str(value),
    )

    if len(digits) != 16:
        return None

    return digits


def mask_card_number(
    value: str,
) -> str:
    """Mask a valid card number."""
    return f"**** **** **** {value[-4:]}"


def normalize_money(
    value: Any,
) -> Decimal | None:
    """Normalize monetary values using Decimal precision."""
    if pd.isna(value):
        return None

    try:
        return Decimal(str(value)).quantize(
            Decimal("0.01"),
        )
    except (
        InvalidOperation,
        ValueError,
        TypeError,
    ):
        return None


def normalize_date_column(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Normalize a date-only column while preserving DATE semantics."""
    result = df.copy()

    parsed = pd.to_datetime(
        result[column],
        errors="coerce",
    )

    result[column] = parsed.dt.date

    return result


def normalize_datetime_column(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """
    Normalize a source timestamp to timezone-aware UTC.

    Source PostgreSQL TIMESTAMP values are naive and represent
    the configured local timezone.
    """
    result = df.copy()

    parsed = pd.to_datetime(
        result[column],
        errors="coerce",
    )

    if isinstance(
        parsed.dtype,
        pd.DatetimeTZDtype,
    ):
        result[column] = parsed.dt.tz_convert("UTC")
    else:
        result[column] = (
            parsed.dt
            .tz_localize(
                SOURCE_TIMEZONE,
                ambiguous="NaT",
                nonexistent="NaT",
            )
            .dt.tz_convert("UTC")
        )

    return result


def process_agencias(
    df: pd.DataFrame,
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean and validate agency data."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["agencias"],
    )

    quarantine(
        rejected,
        "agencias",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    required = [
        "agencia_id",
        "nome_agencia",
        "cidade",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "agencias",
        REJECT_REQUIRED_FIELD_NULL,
        batch_id,
        ingestion_date,
    )

    return df.drop(
        invalid.index[invalid],
    ).copy()


def process_clientes(
    df: pd.DataFrame,
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean and validate customer data."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["clientes"],
    )

    quarantine(
        rejected,
        "clientes",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    df["cpf"] = df["cpf"].apply(
        normalize_cpf,
    )

    required = [
        "cliente_id",
        "nome",
        "cpf",
        "data_nascimento",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "clientes",
        "Required field is null or CPF is invalid.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid].copy()

    duplicated_cpf = df[
        df.duplicated(
            subset=["cpf"],
            keep=False,
        )
    ].copy()

    quarantine(
        duplicated_cpf,
        "clientes",
        "Duplicated CPF.",
        batch_id,
        ingestion_date,
    )

    df = df.drop_duplicates(
        subset=["cpf"],
        keep="last",
    ).copy()

    df = normalize_date_column(
        df,
        "data_nascimento",
    )

    invalid_dates = df[
        df["data_nascimento"].isna()
    ].copy()

    quarantine(
        invalid_dates,
        "clientes",
        "Invalid birth date.",
        batch_id,
        ingestion_date,
    )

    return df.drop(
        invalid_dates.index,
    ).copy()


def process_tipos_transacao(
    df: pd.DataFrame,
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean and validate transaction types."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["tipos_transacao"],
    )

    quarantine(
        rejected,
        "tipos_transacao",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    required = [
        "tipo_transacao_id",
        "descricao",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "tipos_transacao",
        REJECT_REQUIRED_FIELD_NULL,
        batch_id,
        ingestion_date,
    )

    return df[~invalid].copy()


def process_contas(
    df: pd.DataFrame,
    clientes_ids: set[Any],
    agencias_ids: set[Any],
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean and validate bank account data."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["contas"],
    )

    quarantine(
        rejected,
        "contas",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    required = [
        "conta_id",
        "cliente_id",
        "agencia_id",
        "saldo",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "contas",
        REJECT_REQUIRED_FIELD_NULL,
        batch_id,
        ingestion_date,
    )

    df = df[~invalid].copy()

    invalid_cliente = ~df["cliente_id"].isin(
        clientes_ids,
    )

    quarantine(
        df[invalid_cliente],
        "contas",
        "Referenced cliente_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_cliente].copy()

    invalid_agencia = ~df["agencia_id"].isin(
        agencias_ids,
    )

    quarantine(
        df[invalid_agencia],
        "contas",
        "Referenced agencia_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_agencia].copy()

    df["saldo"] = pd.Series(
    [normalize_money(value) for value in df["saldo"]],
    index=df.index,
    dtype="object",
)

    invalid_saldo = df["saldo"].isna()

    quarantine(
        df[invalid_saldo],
        "contas",
        "Invalid monetary value.",
        batch_id,
        ingestion_date,
    )

    return df[~invalid_saldo].copy()


def process_cartoes(
    df: pd.DataFrame,
    contas_ids: set[Any],
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean, validate and mask card data."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["cartoes"],
    )

    quarantine(
        rejected,
        "cartoes",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    df["numero_cartao"] = df[
        "numero_cartao"
    ].apply(normalize_card_number)

    required = [
        "cartao_id",
        "conta_id",
        "numero_cartao",
        "tipo_cartao",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "cartoes",
        "Required field is null or card number is invalid.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid].copy()

    invalid_conta = ~df["conta_id"].isin(
        contas_ids,
    )

    quarantine(
        df[invalid_conta],
        "cartoes",
        "Referenced conta_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_conta].copy()

    valid_card_types = {
        "DEBIT",
        "CREDIT",
    }

    invalid_type = ~df["tipo_cartao"].isin(
        valid_card_types,
    )

    quarantine(
        df[invalid_type],
        "cartoes",
        "Invalid card type.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_type].copy()

    df["numero_cartao_mascarado"] = df[
        "numero_cartao"
    ].apply(mask_card_number)

    return df.drop(
        columns=["numero_cartao"],
    )


def process_emprestimos(
    df: pd.DataFrame,
    clientes_ids: set[Any],
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean and validate loan data."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["emprestimos"],
    )

    quarantine(
        rejected,
        "emprestimos",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    required = [
        "emprestimo_id",
        "cliente_id",
        "valor_contratado",
        "parcelas",
        "data_contrato",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "emprestimos",
        REJECT_REQUIRED_FIELD_NULL,
        batch_id,
        ingestion_date,
    )

    df = df[~invalid].copy()

    invalid_cliente = ~df["cliente_id"].isin(
        clientes_ids,
    )

    quarantine(
        df[invalid_cliente],
        "emprestimos",
        "Referenced cliente_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_cliente].copy()

    df["valor_contratado"] = pd.Series(
        [normalize_money(value) for value in df["valor_contratado"]],
        index=df.index,
        dtype="object",
)
    invalid_value = (
        df["valor_contratado"].isna()
        | (
            df["valor_contratado"]
            <= Decimal(0)
        )
    )

    quarantine(
        df[invalid_value],
        "emprestimos",
        "Loan amount must be greater than zero.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_value].copy()

    valid_installments = {
        6,
        12,
        18,
        24,
        36,
        48,
    }

    invalid_installments = ~df[
        "parcelas"
    ].isin(valid_installments)

    quarantine(
        df[invalid_installments],
        "emprestimos",
        "Invalid installment count.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_installments].copy()

    df = normalize_date_column(
        df,
        "data_contrato",
    )

    invalid_dates = df[
        df["data_contrato"].isna()
    ].copy()

    quarantine(
        invalid_dates,
        "emprestimos",
        "Invalid contract date.",
        batch_id,
        ingestion_date,
    )

    return df.drop(
        invalid_dates.index,
    ).copy()


def process_transacoes(
    df: pd.DataFrame,
    contas_ids: set[Any],
    tipos_transacao_ids: set[Any],
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Clean and validate financial transactions."""
    df = clean_text_columns(df)

    df, rejected = deduplicate_latest(
        df,
        PRIMARY_KEYS["transacoes"],
    )

    quarantine(
        rejected,
        "transacoes",
        REJECT_NULL_OR_DUPLICATED_PK,
        batch_id,
        ingestion_date,
    )

    required = [
        "transacao_id",
        "conta_origem_id",
        "conta_destino_id",
        "tipo_transacao_id",
        "valor",
        "data_hora",
    ]

    invalid = df[required].isna().any(axis=1)

    quarantine(
        df[invalid],
        "transacoes",
        REJECT_REQUIRED_FIELD_NULL,
        batch_id,
        ingestion_date,
    )

    df = df[~invalid].copy()

    invalid_origem = ~df[
        "conta_origem_id"
    ].isin(contas_ids)

    quarantine(
        df[invalid_origem],
        "transacoes",
        "Referenced conta_origem_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_origem].copy()

    invalid_destino = ~df[
        "conta_destino_id"
    ].isin(contas_ids)

    quarantine(
        df[invalid_destino],
        "transacoes",
        "Referenced conta_destino_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_destino].copy()

    invalid_tipo = ~df[
        "tipo_transacao_id"
    ].isin(tipos_transacao_ids)

    quarantine(
        df[invalid_tipo],
        "transacoes",
        "Referenced tipo_transacao_id does not exist.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_tipo].copy()

    same_account = (
        df["conta_origem_id"]
        == df["conta_destino_id"]
    )

    quarantine(
        df[same_account],
        "transacoes",
        "Source and destination accounts must be different.",
        batch_id,
        ingestion_date,
    )

    df = df[~same_account].copy()

    df["valor"] = pd.Series(
        [normalize_money(value) for value in df["valor"]],
        index=df.index,
        dtype="object",
)

    invalid_value = (
        df["valor"].isna()
        | (
            df["valor"]
            <= Decimal(0)
        )
    )

    quarantine(
        df[invalid_value],
        "transacoes",
        "Transaction amount must be greater than zero.",
        batch_id,
        ingestion_date,
    )

    df = df[~invalid_value].copy()

    df = normalize_datetime_column(
        df,
        "data_hora",
    )

    invalid_dates = df[
        df["data_hora"].isna()
    ].copy()

    quarantine(
        invalid_dates,
        "transacoes",
        "Invalid transaction timestamp.",
        batch_id,
        ingestion_date,
    )

    return df.drop(
        invalid_dates.index,
    ).copy()


def write_silver_table(
    df: pd.DataFrame,
    table_name: str,
) -> Path:
    """Write the current cleaned state of a Silver table."""
    table_dir = SILVER_DIR / table_name

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
        "Silver table '%s' written to %s (%d row(s)).",
        table_name,
        file_path,
        len(df),
    )

    return file_path


def run_silver_layer() -> None:
    """Read the latest complete Bronze batch and build Silver tables."""
    logger.info("Starting Silver layer.")

    batch_id, ingestion_date = find_latest_complete_batch()

    raw_data: dict[str, pd.DataFrame] = {}

    for table_name in SOURCE_TABLES:
        df = read_bronze_table(
            table_name,
            batch_id,
        )

        validate_required_columns(
            df,
            table_name,
        )

        raw_data[table_name] = df

    logger.info(
        "Bronze batch loaded successfully | "
        "batch_id=%s | tables=%d",
        batch_id,
        len(raw_data),
    )

    agencias = process_agencias(
        raw_data["agencias"],
        batch_id,
        ingestion_date,
    )

    clientes = process_clientes(
        raw_data["clientes"],
        batch_id,
        ingestion_date,
    )

    tipos_transacao = process_tipos_transacao(
        raw_data["tipos_transacao"],
        batch_id,
        ingestion_date,
    )

    contas = process_contas(
        raw_data["contas"],
        set(clientes["cliente_id"]),
        set(agencias["agencia_id"]),
        batch_id,
        ingestion_date,
    )

    cartoes = process_cartoes(
        raw_data["cartoes"],
        set(contas["conta_id"]),
        batch_id,
        ingestion_date,
    )

    emprestimos = process_emprestimos(
        raw_data["emprestimos"],
        set(clientes["cliente_id"]),
        batch_id,
        ingestion_date,
    )

    transacoes = process_transacoes(
        raw_data["transacoes"],
        set(contas["conta_id"]),
        set(tipos_transacao["tipo_transacao_id"]),
        batch_id,
        ingestion_date,
    )

    silver_data = {
        "agencias": agencias,
        "clientes": clientes,
        "tipos_transacao": tipos_transacao,
        "contas": contas,
        "cartoes": cartoes,
        "emprestimos": emprestimos,
        "transacoes": transacoes,
    }

    for table_name, df in silver_data.items():
        write_silver_table(
            df,
            table_name,
        )

    logger.info(
        "Silver layer completed successfully | "
        "batch_id=%s | tables=%d",
        batch_id,
        len(silver_data),
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv(
            "LOG_LEVEL",
            "INFO",
        ),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    run_silver_layer()