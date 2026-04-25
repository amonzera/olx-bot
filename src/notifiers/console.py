from __future__ import annotations

import logging

from src.core.models import AnalysisResult, Listing
from src.core.prices import format_price

logger = logging.getLogger(__name__)


class ConsoleNotifier:
    def send(self, listing: Listing, analysis: AnalysisResult) -> None:
        flags = ", ".join(flag.value for flag in analysis.flags) or "NO_FLAGS"
        logger.info(
            "Opportunity found: %s | %s | score=%s | flags=%s | %s",
            listing.title,
            format_price(listing.price_cents),
            analysis.score,
            flags,
            listing.url,
        )
        for reason in analysis.reasons:
            logger.info(" - %s", reason)
