from src.bot.app import is_authorized_chat
from src.core.config import Settings


def test_allowed_chat_ids_come_from_allowlist():
    settings = Settings(
        TELEGRAM_ALLOWED_CHAT_IDS="123, 456",
        TELEGRAM_CHAT_ID="999",
    )

    assert settings.allowed_chat_ids == {"123", "456"}


def test_allowed_chat_ids_fall_back_to_telegram_chat_id():
    settings = Settings(
        TELEGRAM_ALLOWED_CHAT_IDS="",
        TELEGRAM_CHAT_ID="999",
    )

    assert settings.allowed_chat_ids == {"999"}


def test_is_authorized_chat():
    assert is_authorized_chat(123, {"123"})
    assert not is_authorized_chat(456, {"123"})
