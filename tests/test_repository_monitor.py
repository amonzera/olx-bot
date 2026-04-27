from datetime import date, datetime

from src.core.models import AlertConfig, AnalysisResult, AnalysisFlag, Listing
from src.storage.sqlite_repository import SQLiteRepository


def test_repository_deduplicates_notifications(tmp_path):
    repository = SQLiteRepository(tmp_path / "monitor.sqlite3")
    alert = AlertConfig(search_term="iphone 13", max_price_cents=250000)
    listing = Listing(
        external_id="111",
        title="iPhone 13",
        price_cents=230000,
        url="https://example.test/111",
        published_at=date(2026, 4, 25),
    )
    analysis = AnalysisResult(
        listing_id="111",
        score=60,
        flags=[AnalysisFlag.RECENT, AnalysisFlag.GOOD_PRICE],
        reasons=["ok"],
        should_notify=True,
    )

    assert not repository.was_notified(alert, listing)
    repository.save_listing(listing)
    repository.mark_notified(alert, listing, analysis)
    assert repository.was_notified(alert, listing)


def test_repository_updates_existing_listing_with_parsed_date(tmp_path):
    repository = SQLiteRepository(tmp_path / "monitor.sqlite3")
    listing = Listing(
        external_id="111",
        title="iPhone 13",
        price_cents=230000,
        url="https://example.test/111",
        published_at=None,
        raw_date="1776601424",
    )
    updated_listing = Listing(
        external_id="111",
        title="iPhone 13",
        price_cents=230000,
        url="https://example.test/111",
        published_at=date(2026, 4, 19),
        raw_date="1776601424",
    )

    repository.save_listing(listing)
    repository.save_listing(updated_listing)

    with repository._connect() as conn:
        row = conn.execute("SELECT published_at FROM listings WHERE external_id = '111'").fetchone()

    assert row["published_at"] == "2026-04-19"


def test_repository_deletes_old_history_without_deleting_alerts(tmp_path):
    repository = SQLiteRepository(tmp_path / "monitor.sqlite3")
    alert = repository.create_alert(
        chat_id="123",
        search_term="iphone 13",
        location="rio de janeiro",
        min_price_cents=150000,
        max_price_cents=250000,
        max_age_days=30,
    )
    analysis = AnalysisResult(
        listing_id="old",
        score=60,
        flags=[AnalysisFlag.RECENT, AnalysisFlag.GOOD_PRICE],
        reasons=["ok"],
        should_notify=True,
    )

    old_listing = Listing(
        external_id="old",
        title="iPhone antigo",
        price_cents=200000,
        url="https://example.test/old",
        published_at=date(2026, 3, 27),
    )
    boundary_listing = Listing(
        external_id="boundary",
        title="iPhone no limite",
        price_cents=210000,
        url="https://example.test/boundary",
        published_at=date(2026, 3, 28),
    )
    unknown_date_listing = Listing(
        external_id="unknown",
        title="iPhone sem data",
        price_cents=220000,
        url="https://example.test/unknown",
        published_at=None,
    )

    repository.save_listing(old_listing)
    repository.save_listing(boundary_listing)
    repository.save_listing(unknown_date_listing)
    repository.mark_notified(alert.to_config(), old_listing, analysis)
    repository.mark_notified(alert.to_config(), boundary_listing, analysis)

    with repository._connect() as conn:
        conn.execute(
            "UPDATE listings SET first_seen_at = ? WHERE external_id = ?",
            ("2026-03-27 11:00:00", "unknown"),
        )
        conn.execute(
            "UPDATE notifications SET notified_at = ? WHERE external_id = ?",
            ("2026-03-27 12:00:00", "old"),
        )
        conn.execute(
            "UPDATE notifications SET notified_at = ? WHERE external_id = ?",
            ("2026-03-28 12:00:00", "boundary"),
        )

    result = repository.delete_old_history(
        30,
        today=date(2026, 4, 27),
        now=datetime(2026, 4, 27, 12, 0, 0),
    )

    assert result.listings_deleted == 2
    assert result.notifications_deleted == 1
    assert repository.list_alerts("123") == [alert]
    with repository._connect() as conn:
        listing_ids = {
            row["external_id"]
            for row in conn.execute("SELECT external_id FROM listings ORDER BY external_id")
        }
        notification_ids = {
            row["external_id"]
            for row in conn.execute("SELECT external_id FROM notifications ORDER BY external_id")
        }

    assert listing_ids == {"boundary"}
    assert notification_ids == {"boundary"}


def test_repository_cruds_alerts(tmp_path):
    repository = SQLiteRepository(tmp_path / "monitor.sqlite3")

    alert = repository.create_alert(
        chat_id="123",
        search_term="iphone 13",
        location="rio de janeiro",
        min_price_cents=150000,
        max_price_cents=250000,
        max_age_days=30,
    )

    assert alert.id > 0
    assert alert.active
    assert repository.list_active_alerts() == [alert]

    updated = repository.update_alert(
        alert_id=alert.id,
        chat_id="123",
        search_term="iphone 14",
        location="brasil",
        min_price_cents=200000,
        max_price_cents=350000,
        max_age_days=30,
    )

    assert updated is not None
    assert updated.search_term == "iphone 14"
    assert updated.location == "brasil"
    assert repository.set_alert_active(alert_id=alert.id, chat_id="123", active=False)
    assert repository.list_active_alerts() == []
    assert repository.delete_alert(alert_id=alert.id, chat_id="123")
