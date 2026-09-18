"""Integration tests for the PostgreSQL banking OLTP database."""

import os

import psycopg2
import pytest

TABLES = (
    "agencias",
    "clientes",
    "tipos_transacao",
    "contas",
    "cartoes",
    "emprestimos",
    "transacoes",
)


def get_connection():
    """Create a PostgreSQL connection from project environment variables."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "15432"),
        dbname=os.getenv("POSTGRES_DB", "banking_oltp"),
        user=os.getenv("POSTGRES_USER", "banking_user"),
        password=os.getenv("POSTGRES_PASSWORD", "change_me"),
    )


@pytest.fixture
def database_connection():
    """Provide a PostgreSQL connection and close it after the test."""
    try:
        connection = get_connection()
    except psycopg2.Error as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")

    yield connection
    connection.close()


def test_expected_tables_exist(database_connection):
    """Verify that all OLTP tables exist."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = ANY(%s)
            """,
            (list(TABLES),),
        )

        existing_tables = {row[0] for row in cursor.fetchall()}

    assert existing_tables == set(TABLES)


@pytest.mark.parametrize("table_name", TABLES)
def test_table_has_data(database_connection, table_name):
    """Verify that each OLTP table contains data."""
    with database_connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]

    assert count > 0


def test_customer_cpf_is_unique(database_connection):
    """Verify that customer CPFs are unique."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*), COUNT(DISTINCT cpf)
            FROM clientes
            """
        )

        total, distinct_cpfs = cursor.fetchone()

    assert total == distinct_cpfs


def test_account_foreign_keys_are_valid(database_connection):
    """Verify account references to customers and agencies."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM contas c
            LEFT JOIN clientes cl
                ON cl.cliente_id = c.cliente_id
            LEFT JOIN agencias a
                ON a.agencia_id = c.agencia_id
            WHERE cl.cliente_id IS NULL
               OR a.agencia_id IS NULL
            """
        )

        invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0


def test_card_foreign_keys_are_valid(database_connection):
    """Verify card references to accounts."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM cartoes c
            LEFT JOIN contas a
                ON a.conta_id = c.conta_id
            WHERE a.conta_id IS NULL
            """
        )

        invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0


def test_loan_foreign_keys_are_valid(database_connection):
    """Verify loan references to customers."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM emprestimos e
            LEFT JOIN clientes c
                ON c.cliente_id = e.cliente_id
            WHERE c.cliente_id IS NULL
            """
        )

        invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0


def test_transaction_foreign_keys_are_valid(database_connection):
    """Verify transaction references."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM transacoes t
            LEFT JOIN contas origem
                ON origem.conta_id = t.conta_origem_id
            LEFT JOIN contas destino
                ON destino.conta_id = t.conta_destino_id
            LEFT JOIN tipos_transacao tipo
                ON tipo.tipo_transacao_id = t.tipo_transacao_id
            WHERE origem.conta_id IS NULL
               OR destino.conta_id IS NULL
               OR tipo.tipo_transacao_id IS NULL
            """
        )

        invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0


def test_transaction_accounts_are_different(database_connection):
    """Verify that source and destination accounts differ."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM transacoes
            WHERE conta_origem_id = conta_destino_id
            """
        )

        invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0


def test_loan_installments_are_positive(database_connection):
    """Verify that loan installments are positive."""
    with database_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM emprestimos
            WHERE parcelas <= 0
            """
        )

        invalid_count = cursor.fetchone()[0]

    assert invalid_count == 0