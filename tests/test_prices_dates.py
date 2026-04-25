from datetime import date

from src.core.dates import is_recent, parse_publication_date
from src.core.prices import parse_price_to_cents


def test_parse_price_to_cents():
    assert parse_price_to_cents("R$ 1.500") == 150000
    assert parse_price_to_cents("1.500,50") == 150050
    assert parse_price_to_cents("A combinar") is None
    assert parse_price_to_cents("") is None


def test_parse_relative_dates_with_fixed_today():
    today = date(2026, 4, 25)

    assert parse_publication_date("hoje", today=today) == date(2026, 4, 25)
    assert parse_publication_date("ontem", today=today) == date(2026, 4, 24)
    assert parse_publication_date("ha 3 semanas", today=today) == date(2026, 4, 4)
    assert parse_publication_date("ha 1 mes", today=today) == date(2026, 3, 26)


def test_recent_window():
    today = date(2026, 4, 25)

    assert is_recent(date(2026, 3, 26), max_age_days=30, today=today)
    assert not is_recent(date(2026, 3, 25), max_age_days=30, today=today)
    assert not is_recent(None, max_age_days=30, today=today)
