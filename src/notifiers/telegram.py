from __future__ import annotations

import logging

from curl_cffi import requests

from src.core.models import AlertConfig, AnalysisResult, Listing
from src.core.prices import format_price

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: str | None = None):
        self.bot_token = bot_token
        self.default_chat_id = default_chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, alert: AlertConfig, listing: Listing, analysis: AnalysisResult) -> None:
        chat_id = alert.chat_id or self.default_chat_id
        if not chat_id:
            logger.warning("Telegram notification skipped because chat_id is not available")
            return

        response = requests.post(
            self.api_url,
            json={
                "chat_id": chat_id,
                "text": self._format_message(alert, listing, analysis),
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if response.status_code >= 400:
            logger.warning("Telegram notification failed: %s %s", response.status_code, response.text)

    def _format_message(self, alert: AlertConfig, listing: Listing, analysis: AnalysisResult) -> str:
        flags = ", ".join(flag.value for flag in analysis.flags) or "NO_FLAGS"
        reasons = "\n".join(f"- {reason}" for reason in analysis.reasons)
        return (
            f"Alerta #{alert.alert_id or '-'}: {alert.search_term} ({alert.location})\n\n"
            f"{listing.title}\n"
            f"{format_price(listing.price_cents)}\n"
            f"Score: {analysis.score}\n"
            f"Flags: {flags}\n"
            f"{reasons}\n\n"
            f"{listing.url}"
        )
