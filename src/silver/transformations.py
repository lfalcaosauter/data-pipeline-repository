import re
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

from silver.config import (
    PRIMARY_KEYS,
    REJECT_NULL_OR_DUPLICATED_PK,
    REJECT_REQUIRED_FIELD_NULL,
    SOURCE_TIMEZONE,
)
from silver.io import quarantine


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


def deduplicate_latest(
    df: pd.DataFrame,
    primary_key: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep the latest Bronze version of each primary key."""
    valid = df[df[primary_key].notna()].copy()
    invalid = df[df[primary_key].isna()].copy()

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

    return df[~invalid].copy()


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
        [
            normalize_money(value)
            for value in df["saldo"]
        ],
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
        [
            normalize_money(value)
            for value in df["valor_contratado"]
        ],
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
        [
            normalize_money(value)
            for value in df["valor"]
        ],
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