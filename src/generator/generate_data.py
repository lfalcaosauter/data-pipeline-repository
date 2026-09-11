import logging
import os
from datetime import UTC, datetime
from decimal import Decimal

import psycopg2
from dotenv import load_dotenv
from faker import Faker

load_dotenv()

logger = logging.getLogger(__name__)

fake = Faker("pt_BR")

SEED = int(os.getenv("FAKER_SEED", "42"))

NUM_AGENCIAS = int(os.getenv("NUM_AGENCIAS", "10"))
NUM_CLIENTES = int(os.getenv("NUM_CLIENTES", "1000"))
NUM_CONTAS = int(os.getenv("NUM_CONTAS", "1200"))
NUM_CARTOES = int(os.getenv("NUM_CARTOES", "900"))
NUM_EMPRESTIMOS = int(os.getenv("NUM_EMPRESTIMOS", "400"))
NUM_TRANSACOES = int(os.getenv("NUM_TRANSACOES", "10000"))

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "banking_oltp")
DB_USER = os.getenv("POSTGRES_USER", "banking_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change_me")


def generate_cpf() -> str:
    """Generate a unique 11-digit synthetic CPF."""
    return fake.numerify(text="###########")


def generate_card_number() -> str:
    """Generate a unique 16-digit synthetic card number."""
    return fake.numerify(text="################")


def generate_transaction_datetime(
    start_year: int = 2024,
) -> datetime:
    """Generate a random transaction timestamp."""
    start = datetime(start_year, 1, 1, tzinfo=UTC)
    end = datetime.now(UTC)

    return fake.date_time_between(
        start_date=start,
        end_date=end,
    )


def generate_money(minimum_cents: int, maximum_cents: int) -> Decimal:
    """Generate a monetary value with two decimal places."""
    cents = fake.random_int(
        min=minimum_cents,
        max=maximum_cents,
    )
    return Decimal(cents) / Decimal(100)


def clear_tables(cursor) -> None:
    """Clear generated data from all OLTP tables."""
    cursor.execute(
        """
        TRUNCATE TABLE
            transacoes,
            emprestimos,
            cartoes,
            contas,
            tipos_transacao,
            clientes,
            agencias
        RESTART IDENTITY CASCADE;
        """
    )


def insert_agencias(cursor) -> None:
    """Insert synthetic bank branches."""
    data = [
        (
            agencia_id,
            f"Agência {agencia_id:03d}",
            fake.city(),
        )
        for agencia_id in range(1, NUM_AGENCIAS + 1)
    ]

    cursor.executemany(
        """
        INSERT INTO agencias (
            agencia_id,
            nome_agencia,
            cidade
        )
        VALUES (%s, %s, %s)
        """,
        data,
    )


def insert_clientes(cursor) -> None:
    """Insert synthetic customers."""
    data = []
    used_cpfs: set[str] = set()

    for cliente_id in range(1, NUM_CLIENTES + 1):
        cpf = generate_cpf()

        while cpf in used_cpfs:
            cpf = generate_cpf()

        used_cpfs.add(cpf)

        data.append(
            (
                cliente_id,
                fake.name(),
                cpf,
                fake.date_of_birth(
                    minimum_age=18,
                    maximum_age=80,
                ),
            )
        )

    cursor.executemany(
        """
        INSERT INTO clientes (
            cliente_id,
            nome,
            cpf,
            data_nascimento
        )
        VALUES (%s, %s, %s, %s)
        """,
        data,
    )


def insert_tipos_transacao(cursor) -> None:
    """Insert transaction types defined by the project."""
    data = [
        (1, "PIX"),
        (2, "TED"),
        (3, "DOC"),
        (4, "SAQUE"),
        (5, "DEPOSITO"),
    ]

    cursor.executemany(
        """
        INSERT INTO tipos_transacao (
            tipo_transacao_id,
            descricao
        )
        VALUES (%s, %s)
        """,
        data,
    )


def insert_contas(cursor) -> None:
    """Insert synthetic bank accounts."""
    data = []

    for conta_id in range(1, NUM_CONTAS + 1):
        cliente_id = fake.random_int(
            min=1,
            max=NUM_CLIENTES,
        )
        agencia_id = fake.random_int(
            min=1,
            max=NUM_AGENCIAS,
        )
        saldo = generate_money(
            minimum_cents=0,
            maximum_cents=5_000_000,
        )

        data.append(
            (
                conta_id,
                cliente_id,
                agencia_id,
                saldo,
            )
        )

    cursor.executemany(
        """
        INSERT INTO contas (
            conta_id,
            cliente_id,
            agencia_id,
            saldo
        )
        VALUES (%s, %s, %s, %s)
        """,
        data,
    )


def insert_cartoes(cursor) -> None:
    """Insert synthetic bank cards."""
    data = []
    used_cards: set[str] = set()

    for cartao_id in range(1, NUM_CARTOES + 1):
        conta_id = fake.random_int(
            min=1,
            max=NUM_CONTAS,
        )

        numero_cartao = generate_card_number()

        while numero_cartao in used_cards:
            numero_cartao = generate_card_number()

        used_cards.add(numero_cartao)

        tipo_cartao = fake.random_element(
            elements=("DEBIT", "CREDIT"),
        )

        data.append(
            (
                cartao_id,
                conta_id,
                numero_cartao,
                tipo_cartao,
            )
        )

    cursor.executemany(
        """
        INSERT INTO cartoes (
            cartao_id,
            conta_id,
            numero_cartao,
            tipo_cartao
        )
        VALUES (%s, %s, %s, %s)
        """,
        data,
    )


def insert_emprestimos(cursor) -> None:
    """Insert synthetic loans."""
    data = []

    for emprestimo_id in range(1, NUM_EMPRESTIMOS + 1):
        cliente_id = fake.random_int(
            min=1,
            max=NUM_CLIENTES,
        )

        valor_contratado = generate_money(
            minimum_cents=100_000,
            maximum_cents=10_000_000,
        )

        parcelas = fake.random_element(
            elements=(6, 12, 18, 24, 36, 48),
        )

        data_contrato = fake.date_between(
            start_date="-3y",
            end_date="today",
        )

        data.append(
            (
                emprestimo_id,
                cliente_id,
                valor_contratado,
                parcelas,
                data_contrato,
            )
        )

    cursor.executemany(
        """
        INSERT INTO emprestimos (
            emprestimo_id,
            cliente_id,
            valor_contratado,
            parcelas,
            data_contrato
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        data,
    )


def insert_transacoes(cursor) -> None:
    """Insert synthetic financial transactions."""
    data = []

    for transacao_id in range(1, NUM_TRANSACOES + 1):
        conta_origem_id = fake.random_int(
            min=1,
            max=NUM_CONTAS,
        )

        conta_destino_id = fake.random_int(
            min=1,
            max=NUM_CONTAS,
        )

        while conta_destino_id == conta_origem_id:
            conta_destino_id = fake.random_int(
                min=1,
                max=NUM_CONTAS,
            )

        tipo_transacao_id = fake.random_int(
            min=1,
            max=5,
        )

        valor = generate_money(
            minimum_cents=1_000,
            maximum_cents=1_000_000,
        )

        data_hora = generate_transaction_datetime()

        data.append(
            (
                transacao_id,
                conta_origem_id,
                conta_destino_id,
                tipo_transacao_id,
                valor,
                data_hora,
            )
        )

    cursor.executemany(
        """
        INSERT INTO transacoes (
            transacao_id,
            conta_origem_id,
            conta_destino_id,
            tipo_transacao_id,
            valor,
            data_hora
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        data,
    )


def main() -> None:
    """Generate and load synthetic banking data."""
    Faker.seed(SEED)

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    try:
        with connection, connection.cursor() as cursor:
            logger.info("Clearing existing generated data.")
            clear_tables(cursor)

            logger.info("Inserting agencies.")
            insert_agencias(cursor)

            logger.info("Inserting customers.")
            insert_clientes(cursor)

            logger.info("Inserting transaction types.")
            insert_tipos_transacao(cursor)

            logger.info("Inserting accounts.")
            insert_contas(cursor)

            logger.info("Inserting cards.")
            insert_cartoes(cursor)

            logger.info("Inserting loans.")
            insert_emprestimos(cursor)

            logger.info("Inserting transactions.")
            insert_transacoes(cursor)

        logger.info("Synthetic data generation completed successfully.")

    except Exception:
        logger.exception("Synthetic data generation failed.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    main()