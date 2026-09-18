import logging

from faker import Faker

from config import (
    FAKER_LOCALE,
    FAKER_SEED,
    LOG_LEVEL,
    NUM_AGENCIAS,
    NUM_CARTOES,
    NUM_CLIENTES,
    NUM_CONTAS,
    NUM_EMPRESTIMOS,
    NUM_TRANSACOES,
)
from generator.accounts import insert_contas
from generator.cards import insert_cartoes
from generator.customers import insert_clientes
from generator.helpers import get_next_id
from generator.loans import insert_emprestimos
from generator.transactions import insert_transacoes
from utils.database import get_database_connection

logger = logging.getLogger(__name__)

fake = Faker(FAKER_LOCALE)


def insert_agencias(
    cursor,
    start_id: int,
) -> None:
    """Insert synthetic bank branches."""
    data = [
        (
            agencia_id,
            f"Agência {agencia_id:03d}",
            fake.city(),
        )
        for agencia_id in range(
            start_id,
            start_id + NUM_AGENCIAS,
        )
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


def main() -> None:
    """Generate and load synthetic banking data."""
    Faker.seed(FAKER_SEED)

    connection = get_database_connection()

    try:
        with connection, connection.cursor() as cursor:
            agencia_start_id = get_next_id(
                cursor,
                "agencias",
                "agencia_id",
            )

            cliente_start_id = get_next_id(
                cursor,
                "clientes",
                "cliente_id",
            )

            conta_start_id = get_next_id(
                cursor,
                "contas",
                "conta_id",
            )

            cartao_start_id = get_next_id(
                cursor,
                "cartoes",
                "cartao_id",
            )

            emprestimo_start_id = get_next_id(
                cursor,
                "emprestimos",
                "emprestimo_id",
            )

            transacao_start_id = get_next_id(
                cursor,
                "transacoes",
                "transacao_id",
            )

            logger.info(
                "Starting synthetic data generation."
            )

            logger.info(
                "Inserting %s agencies.",
                NUM_AGENCIAS,
            )
            insert_agencias(
                cursor,
                agencia_start_id,
            )

            logger.info(
                "Inserting %s customers.",
                NUM_CLIENTES,
            )
            insert_clientes(
                cursor,
                fake,
                cliente_start_id,
            )

            logger.info(
                "Inserting %s accounts.",
                NUM_CONTAS,
            )
            insert_contas(
                cursor,
                fake,
                conta_start_id,
                cliente_start_id,
                cliente_start_id + NUM_CLIENTES - 1,
                agencia_start_id,
                agencia_start_id + NUM_AGENCIAS - 1,
            )

            logger.info(
                "Inserting %s cards.",
                NUM_CARTOES,
            )
            insert_cartoes(
                cursor,
                fake,
                cartao_start_id,
                conta_start_id,
                conta_start_id + NUM_CONTAS - 1,
            )

            logger.info(
                "Inserting %s loans.",
                NUM_EMPRESTIMOS,
            )
            insert_emprestimos(
                cursor,
                fake,
                emprestimo_start_id,
                cliente_start_id,
                cliente_start_id + NUM_CLIENTES - 1,
            )

            logger.info(
                "Inserting %s transactions.",
                NUM_TRANSACOES,
            )
            insert_transacoes(
                cursor,
                fake,
                transacao_start_id,
                conta_start_id,
                conta_start_id + NUM_CONTAS - 1,
            )

        logger.info(
            "Synthetic data generation completed successfully."
        )

    except Exception:
        logger.exception(
            "Synthetic data generation failed."
        )
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=LOG_LEVEL,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    main()

