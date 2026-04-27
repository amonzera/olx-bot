from __future__ import annotations

from dataclasses import dataclass

from src.core.dates import normalize_text
from src.core.models import Alert, SearchLocation
from src.core.prices import format_price, parse_price_to_cents


@dataclass(slots=True)
class AlertDraft:
    search_term: str
    location: str
    min_price_cents: int
    max_price_cents: int


def command_payload(text: str | None) -> str:
    if not text:
        return ""
    parts = text.strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def parse_alert_payload(payload: str) -> AlertDraft:
    parts = [part.strip() for part in payload.split("|")]
    if len(parts) != 4:
        raise ValueError(
            "Use: /add produto | brasil ou rio de janeiro | preço mínimo | preço máximo"
        )

    search_term, location_text, min_price_text, max_price_text = parts
    if not search_term:
        raise ValueError("Informe o nome do produto.")

    location = normalize_location(location_text)
    min_price_cents = parse_price_to_cents(min_price_text)
    max_price_cents = parse_price_to_cents(max_price_text)

    if min_price_cents is None or max_price_cents is None:
        raise ValueError("Informe preços válidos, como 1500 ou 1.500,00.")
    if min_price_cents < 0 or max_price_cents <= 0:
        raise ValueError("A faixa de preço precisa ter valores positivos.")
    if min_price_cents > max_price_cents:
        raise ValueError("O preço mínimo não pode ser maior que o preço máximo.")

    return AlertDraft(
        search_term=search_term,
        location=location,
        min_price_cents=min_price_cents,
        max_price_cents=max_price_cents,
    )


def parse_edit_payload(payload: str) -> tuple[int, AlertDraft]:
    parts = [part.strip() for part in payload.split("|")]
    if len(parts) != 5:
        raise ValueError(
            "Use: /edit id | produto | brasil ou rio de janeiro | preço mínimo | preço máximo"
        )

    try:
        alert_id = int(parts[0])
    except ValueError as exc:
        raise ValueError("Informe um ID numérico para editar o alerta.") from exc

    return alert_id, parse_alert_payload(" | ".join(parts[1:]))


def parse_alert_id(payload: str) -> int:
    try:
        return int(payload.strip())
    except ValueError as exc:
        raise ValueError("Informe o ID numérico do alerta.") from exc


def normalize_location(value: str) -> str:
    normalized = normalize_text(value).strip()
    normalized = " ".join(normalized.split())
    aliases = {
        "br": SearchLocation.BRASIL.value,
        "brasil": SearchLocation.BRASIL.value,
        "todo brasil": SearchLocation.BRASIL.value,
        "rio": SearchLocation.RIO_DE_JANEIRO.value,
        "rj": SearchLocation.RIO_DE_JANEIRO.value,
        "estado rj": SearchLocation.RIO_DE_JANEIRO.value,
        "estado do rj": SearchLocation.RIO_DE_JANEIRO.value,
        "rio de janeiro": SearchLocation.RIO_DE_JANEIRO.value,
        "estado rio de janeiro": SearchLocation.RIO_DE_JANEIRO.value,
        "estado do rio de janeiro": SearchLocation.RIO_DE_JANEIRO.value,
    }
    if normalized not in aliases:
        raise ValueError("Localidade inválida. Use brasil ou rio de janeiro.")
    return aliases[normalized]


def format_alert(alert: Alert) -> str:
    status = "ativo" if alert.active else "pausado"
    last_scan = alert.last_scan_at.strftime("%d/%m/%Y %H:%M") if alert.last_scan_at else "nunca"
    return (
        f"#{alert.id} - {alert.search_term}\n"
        f"Local: {alert.location}\n"
        f"Preço: {format_price(alert.min_price_cents)} até {format_price(alert.max_price_cents)}\n"
        f"Status: {status}\n"
        f"Última busca: {last_scan}"
    )


HELP_TEXT = """Comandos disponíveis:

/add produto | brasil ou rio de janeiro | preço mínimo | preço máximo
Cria um alerta e faz uma busca inicial dos anúncios dos últimos 30 dias.
Exemplo: /add iphone 13 | rio de janeiro | 1500 | 2500

/list
Lista seus alertas.

/edit id | produto | brasil ou rio de janeiro | preço mínimo | preço máximo
Altera um alerta e faz uma nova busca.
Exemplo: /edit 2 | macbook air m1 | brasil | 3000 | 4500

/delete id
Exclui um alerta.

/pause id
Pausa um alerta.

/resume id
Reativa um alerta.

/help
Mostra esta ajuda."""
