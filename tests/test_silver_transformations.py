"""Unit tests for Silver transformation functions."""

import pandas as pd

from silver.transformations import (
    process_agencias,
    process_cartoes,
    process_clientes,
    process_contas,
    process_emprestimos,
    process_tipos_transacao,
    process_transacoes,
)


def test_process_agencias_removes_invalid_rows():
    """Reject agencies with null primary keys."""
    df = pd.DataFrame(
        {
            "agencia_id": [1, None, 3],
            "nome_agencia": ["Agencia Central", "Agencia Invalida", "Agencia Norte"],
            "cidade": ["Recife", "Natal", "Maceio"],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_agencias(
        df,
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 2
    assert result["agencia_id"].notna().all()


def test_process_agencias_removes_duplicates():
    """Keep only the latest record for duplicated agency IDs."""
    df = pd.DataFrame(
        {
            "agencia_id": [1, 1, 2],
            "nome_agencia": [
                "Agencia Antiga",
                "Agencia Atual",
                "Agencia Norte",
            ],
            "cidade": ["Recife", "Recife", "Maceio"],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-15 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                ]
            ),
        }
    )

    result = process_agencias(
        df,
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 2

    agencia = result[result["agencia_id"] == 1].iloc[0]

    assert agencia["nome_agencia"] == "Agencia Atual"


def test_process_clientes_removes_null_primary_keys():
    """Reject customers without a customer ID."""
    df = pd.DataFrame(
        {
            "cliente_id": [1, None, 3],
            "nome": ["Ana Silva", "Cliente Invalido", "Carlos Souza"],
            "cpf": ["12345678901", "12345678902", "12345678903"],
            "data_nascimento": pd.to_datetime(
                ["1990-01-01", "1991-01-01", "1992-01-01"]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_clientes(
        df,
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 2
    assert result["cliente_id"].notna().all()


def test_process_tipos_transacao_removes_duplicates():
    """Keep one record for duplicated transaction types."""
    df = pd.DataFrame(
        {
            "tipo_transacao_id": [1, 1, 2],
            "descricao": ["PIX", "PIX", "TED"],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-15 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                ]
            ),
        }
    )

    result = process_tipos_transacao(
        df,
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 2
    assert set(result["tipo_transacao_id"]) == {1, 2}

def test_process_contas_removes_invalid_client_relationship():
    """Reject accounts referencing a non-existent customer."""
    df = pd.DataFrame(
        {
            "conta_id": [1, 2],
            "cliente_id": [1, 999],
            "agencia_id": [10, 10],
            "saldo": [1000.00, 500.00],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_contas(
    df,
    clientes_ids={1},
    agencias_ids={10},
    batch_id="test-batch",
    ingestion_date="2026-09-16",
)

    assert len(result) == 1
    assert result.iloc[0]["cliente_id"] == 1


def test_process_contas_removes_invalid_agency_relationship():
    """Reject accounts referencing a non-existent agency."""
    df = pd.DataFrame(
        {
            "conta_id": [1, 2],
            "cliente_id": [1, 2],
            "agencia_id": [10, 999],
            "saldo": [1000.00, 500.00],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_contas(
    df,
    clientes_ids={1, 2},
    agencias_ids={10},
    batch_id="test-batch",
    ingestion_date="2026-09-16",
)

    assert len(result) == 1
    assert result.iloc[0]["agencia_id"] == 10

def test_process_cartoes_removes_invalid_account_relationship():
    """Reject cards referencing a non-existent account."""
    df = pd.DataFrame(
        {
            "cartao_id": [1, 2],
            "conta_id": [100, 999],
            "numero_cartao": ["1234567890123456", "6543210987654321"],
            "tipo_cartao": ["DEBIT", "CREDIT"],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_cartoes(
        df,
        contas_ids={100},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["conta_id"] == 100


def test_process_cartoes_removes_duplicates():
    """Keep the latest record for duplicated card IDs."""
    df = pd.DataFrame(
        {
            "cartao_id": [1, 1, 2],
            "conta_id": [100, 100, 200],
            "numero_cartao": [
                "1234567890123456",
                "1234567890123456",
                "6543210987654321",
            ],
            "tipo_cartao": ["DEBIT", "CREDIT", "DEBIT"],
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-15 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                ]
            ),
        }
    )

    result = process_cartoes(
        df,
        contas_ids={100, 200},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 2

    cartao = result[result["cartao_id"] == 1].iloc[0]

    assert cartao["tipo_cartao"] == "CREDIT"

def test_process_emprestimos_removes_invalid_client_relationship():
    """Reject loans referencing a non-existent customer."""
    df = pd.DataFrame(
        {
            "emprestimo_id": [1, 2],
            "cliente_id": [1, 999],
            "valor_contratado": [10000.00, 20000.00],
            "parcelas": [12, 24],
            "data_contrato": pd.to_datetime(
                ["2026-01-01", "2026-01-02"]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_emprestimos(
        df,
        clientes_ids={1},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["cliente_id"] == 1


def test_process_emprestimos_removes_invalid_installments():
    """Reject loans with zero or negative installments."""
    df = pd.DataFrame(
        {
            "emprestimo_id": [1, 2, 3],
            "cliente_id": [1, 2, 3],
            "valor_contratado": [10000.00, 20000.00, 30000.00],
            "parcelas": [12, 0, -5],
            "data_contrato": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-02",
                    "2026-01-03",
                ]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_emprestimos(
        df,
        clientes_ids={1, 2, 3},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["parcelas"] == 12

def test_process_transacoes_removes_invalid_account_relationship():
    """Reject transactions referencing non-existent accounts."""
    df = pd.DataFrame(
        {
            "transacao_id": [1, 2],
            "conta_origem_id": [100, 999],
            "conta_destino_id": [200, 200],
            "tipo_transacao_id": [1, 1],
            "valor": [100.00, 200.00],
            "data_hora": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                ]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_transacoes(
        df,
        contas_ids={100, 200},
        tipos_transacao_ids={1},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["conta_origem_id"] == 100


def test_process_transacoes_rejects_same_origin_and_destination():
    """Reject transactions using the same account as origin and destination."""
    df = pd.DataFrame(
        {
            "transacao_id": [1, 2],
            "conta_origem_id": [100, 200],
            "conta_destino_id": [100, 300],
            "tipo_transacao_id": [1, 1],
            "valor": [100.00, 200.00],
            "data_hora": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                ]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_transacoes(
        df,
        contas_ids={100, 200, 300},
        tipos_transacao_ids={1},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["transacao_id"] == 2

def test_process_transacoes_removes_non_positive_values():
    """Reject transactions with non-positive values."""
    df = pd.DataFrame(
        {
            "transacao_id": [1, 2, 3],
            "conta_origem_id": [100, 101, 102],
            "conta_destino_id": [200, 201, 202],
            "tipo_transacao_id": [1, 1, 1],
            "valor": [100.00, 0.00, -50.00],
            "data_hora": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 11:00:00",
                    "2026-09-16 12:00:00",
                ]
            ),
            "_ingestion_timestamp": pd.to_datetime(
                [
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                    "2026-09-16 10:00:00",
                ]
            ),
        }
    )

    result = process_transacoes(
        df,
        contas_ids={100, 101, 102, 200, 201, 202},
        tipos_transacao_ids={1},
        batch_id="test-batch",
        ingestion_date="2026-09-16",
    )

    assert len(result) == 1
    assert result.iloc[0]["transacao_id"] == 1
    assert result.iloc[0]["valor"] == 100.00