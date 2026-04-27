import pytest

from src.bot.commands import normalize_location, parse_alert_id, parse_alert_payload, parse_edit_payload


def test_parse_alert_payload():
    draft = parse_alert_payload("iphone 13 | rio de janeiro | 1500 | 2500")

    assert draft.search_term == "iphone 13"
    assert draft.location == "rio de janeiro"
    assert draft.min_price_cents == 150000
    assert draft.max_price_cents == 250000


def test_parse_edit_payload():
    alert_id, draft = parse_edit_payload("7 | macbook air | brasil | 3000 | 4500")

    assert alert_id == 7
    assert draft.search_term == "macbook air"
    assert draft.location == "brasil"


def test_parse_alert_payload_rejects_invalid_range():
    with pytest.raises(ValueError, match="mínimo"):
        parse_alert_payload("iphone 13 | brasil | 3000 | 2000")


def test_parse_alert_id_rejects_text():
    with pytest.raises(ValueError, match="ID"):
        parse_alert_id("abc")


def test_normalize_location_aliases():
    assert normalize_location("RJ") == "rio de janeiro"
    assert normalize_location("todo brasil") == "brasil"
