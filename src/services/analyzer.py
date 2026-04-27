from __future__ import annotations

import re
from datetime import date

from src.core.dates import is_recent, normalize_text
from src.core.models import AlertConfig, AnalysisFlag, AnalysisResult, Listing


class OpportunityAnalyzer:
    """Classifies listings without hiding risky opportunities from the user."""

    defect_patterns = [
        r"\bcom defeito\b",
        r"\bquebrad[oa]\b",
        r"\btrincad[oa]\b",
        r"\bpecas?\b",
        r"\bn[aã]o liga\b",
        r"\bvenda de pecas?\b",
        r"\bsomente placa\b",
        r"\bbloquead[oa]\b",
        r"\bcom avaria\b",
        r"\bprecisa arrumar\b",
        r"\bdisplay\b",
        r"\bbateria viciada\b",
    ]

    scam_patterns = [
        r"\bpassar cart[aã]o\b",
        r"\bsinal\b",
        r"\bentrada\b",
        r"\bsem nota\b",
        r"\bconta bloqueada\b",
    ]

    safe_context_patterns = [
        r"\bsem defeito\b",
        r"\bn[aã]o tem defeito\b",
        r"\bdisplay perfeito\b",
        r"\bbateria boa\b",
    ]

    def analyze(
        self,
        listing: Listing,
        alert_config: AlertConfig,
        today: date | None = None,
    ) -> AnalysisResult:
        flags: list[AnalysisFlag] = []
        reasons: list[str] = []
        score = 0

        title = normalize_text(listing.title)

        if listing.published_at is None:
            flags.append(AnalysisFlag.UNKNOWN_DATE)
            reasons.append("Data de publicacao nao identificada; nao notificar por padrao.")
        elif is_recent(listing.published_at, alert_config.max_age_days, today=today):
            flags.append(AnalysisFlag.RECENT)
            reasons.append(f"Publicado dentro da janela de {alert_config.max_age_days} dias.")
            score += 20
        else:
            reasons.append(f"Publicado ha mais de {alert_config.max_age_days} dias.")

        if listing.price_cents is not None:
            below_min = (
                alert_config.min_price_cents is not None
                and listing.price_cents < alert_config.min_price_cents
            )
            above_max = (
                alert_config.max_price_cents is not None
                and listing.price_cents > alert_config.max_price_cents
            )
            if below_min:
                reasons.append("Preco esta abaixo do minimo configurado para o alerta.")
            elif above_max:
                reasons.append("Preco esta acima do maximo configurado para o alerta.")
            else:
                target_price = alert_config.target_price_cents or alert_config.max_price_cents
                has_price_rule = (
                    alert_config.min_price_cents is not None
                    or alert_config.max_price_cents is not None
                    or target_price is not None
                )
                if has_price_rule and (target_price is None or listing.price_cents <= target_price):
                    flags.append(AnalysisFlag.GOOD_PRICE)
                    reasons.append("Preco esta dentro da faixa configurada.")
                    score += 40

            if (
                alert_config.min_expected_price_cents is not None
                and listing.price_cents < alert_config.min_expected_price_cents
            ):
                flags.append(AnalysisFlag.LOW_PRICE_CAUTION)
                flags.append(AnalysisFlag.SCAM_CAUTION)
                reasons.append("Preco muito abaixo do minimo esperado; revisar com cuidado.")
                score += 15

        if not self._has_safe_context(title):
            if self._matches_any(title, self.defect_patterns):
                flags.append(AnalysisFlag.DEFECT_KEYWORD)
                reasons.append("Titulo sugere defeito, peca, bloqueio ou reparo.")
                score -= 10

        if self._matches_any(title, self.scam_patterns):
            flags.append(AnalysisFlag.SCAM_CAUTION)
            reasons.append("Titulo contem termo que merece cautela antes do contato.")
            score -= 5

        flags = list(dict.fromkeys(flags))
        should_notify = AnalysisFlag.RECENT in flags and AnalysisFlag.GOOD_PRICE in flags

        return AnalysisResult(
            listing_id=listing.external_id,
            score=max(score, 0),
            flags=flags,
            reasons=reasons,
            should_notify=should_notify,
        )

    def _has_safe_context(self, text: str) -> bool:
        return self._matches_any(text, self.safe_context_patterns)

    def _matches_any(self, text: str, patterns: list[str]) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)
