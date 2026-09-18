"""Unit tests for the synthetic banking data generator."""

from datetime import datetime
from decimal import Decimal

from faker import Faker

from generator.helpers import (
    generate_card_number,
    generate_cpf,
    generate_money,
    generate_transaction_datetime,
)

fake = Faker("pt_BR")


def test_generate_cpf_has_eleven_digits():
    cpf = generate_cpf(fake)

    assert len(cpf) == 11
    assert cpf.isdigit()


def test_generate_card_number_has_sixteen_digits():
    card_number = generate_card_number(fake)

    assert len(card_number) == 16
    assert card_number.isdigit()


def test_generate_money_returns_decimal():
    value = generate_money(
        fake,
        minimum_cents=100,
        maximum_cents=10000,
    )

    assert isinstance(value, Decimal)
    assert Decimal(1) <= value <= Decimal(100)


def test_generate_transaction_datetime_is_naive():
    value = generate_transaction_datetime(fake)

    assert isinstance(value, datetime)
    assert value.tzinfo is None


def test_generate_transaction_datetime_is_not_in_the_future():
    value = generate_transaction_datetime(fake)

    current_datetime = datetime.now().astimezone().replace(tzinfo=None)
    assert value <= current_datetime


def test_generate_transaction_datetime_respects_start_year():
    value = generate_transaction_datetime(
        fake,
        start_year=2024,
    )

    start_date = datetime(2024, 1, 1).astimezone().replace(tzinfo=None)
    assert value >= start_date