from datetime import date

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
