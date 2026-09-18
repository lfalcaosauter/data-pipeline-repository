from faker import Faker

from config import NUM_CARTOES
from generator.helpers import generate_card_number


def get_existing_card_numbers(cursor) -> set[str]:
    """Return all card numbers already stored in the database."""
    cursor.execute(
        """
        SELECT numero_cartao
        FROM cartoes
        """
    )

    return {
        row[0]
        for row in cursor.fetchall()
    }


def insert_cartoes(
    cursor,
    fake: Faker,
    start_id: int,
    conta_min_id: int,
    conta_max_id: int,
) -> None:
    """Insert synthetic bank cards."""
    data = []
    used_cards: set[str] = set()
    existing_cards = get_existing_card_numbers(cursor)

    for cartao_id in range(
        start_id,
        start_id + NUM_CARTOES,
    ):
        conta_id = fake.random_int(
            min=conta_min_id,
            max=conta_max_id,
        )

        numero_cartao = generate_card_number(fake)

        while (
            numero_cartao in used_cards
            or numero_cartao in existing_cards
        ):
            numero_cartao = generate_card_number(fake)

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
