from __future__ import annotations

import logging

from curl_cffi import requests

from src.core.models import AnalysisResult, Listing
from src.core.prices import format_price

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send(self, listing: Listing, analysis: AnalysisResult) -> None:
        response = requests.post(
            self.api_url,
            json={
                "chat_id": self.chat_id,
                "text": self._format_message(listing, analysis),
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        if response.status_code >= 400:
            logger.warning("Telegram notification failed: %s %s", response.status_code, response.text)

    def _format_message(self, listing: Listing, analysis: AnalysisResult) -> str:
        flags = ", ".join(flag.value for flag in analysis.flags) or "NO_FLAGS"
        reasons = "\n".join(f"- {reason}" for reason in analysis.reasons)
        return (
            f"{listing.title}\n"
            f"{format_price(listing.price_cents)}\n"
            f"Score: {analysis.score}\n"
            f"Flags: {flags}\n"
            f"{reasons}\n\n"
            f"{listing.url}"
        )
