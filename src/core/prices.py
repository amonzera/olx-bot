from __future__ import annotations

import re


def parse_price_to_cents(value: object) -> int | None:
    """Normalize Brazilian price strings to integer cents."""
    if value is None:
        return None

    if isinstance(value, int):
        return value * 100

    if isinstance(value, float):
        return int(round(value * 100))

    text = str(value).strip().lower()
    if not text or "combinar" in text:
        return None

    cleaned = re.sub(r"[^\d,\.]", "", text)
    if not cleaned:
        return None

    if "," in cleaned:
        integer_part, decimal_part = cleaned.rsplit(",", 1)
        integer_part = integer_part.replace(".", "")
        decimal_part = (decimal_part + "00")[:2]
        return int(integer_part or "0") * 100 + int(decimal_part)

    return int(cleaned.replace(".", "")) * 100


def format_price(cents: int | None) -> str:
    if cents is None:
        return "A combinar"
    reais, centavos = divmod(cents, 100)
    reais_text = f"{reais:,}".replace(",", ".")
    return f"R$ {reais_text},{centavos:02d}"
