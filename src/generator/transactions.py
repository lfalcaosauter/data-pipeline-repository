from faker import Faker

from config import NUM_TRANSACOES
from generator.helpers import (
    generate_money,
    generate_transaction_datetime,
)


def insert_transacoes(
    cursor,
    fake: Faker,
    start_id: int,
    conta_min_id: int,
    conta_max_id: int,
) -> None:
    """Insert synthetic financial transactions."""
    data = []

    for transacao_id in range(
        start_id,
        start_id + NUM_TRANSACOES,
    ):
        conta_origem_id = fake.random_int(
            min=conta_min_id,
            max=conta_max_id,
        )

        conta_destino_id = fake.random_int(
            min=conta_min_id,
            max=conta_max_id,
        )

        while conta_destino_id == conta_origem_id:
            conta_destino_id = fake.random_int(
                min=conta_min_id,
                max=conta_max_id,
            )

        tipo_transacao_id = fake.random_int(
            min=1,
            max=5,
        )

        valor = generate_money(
            fake,
            minimum_cents=1_000,
            maximum_cents=1_000_000,
        )

        data_hora = generate_transaction_datetime(fake)

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
