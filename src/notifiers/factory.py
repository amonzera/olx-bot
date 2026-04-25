from __future__ import annotations

from src.core.config import settings
from src.notifiers.console import ConsoleNotifier
from src.notifiers.telegram import TelegramNotifier


def build_notifier():
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        return TelegramNotifier(settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID)
    return ConsoleNotifier()
