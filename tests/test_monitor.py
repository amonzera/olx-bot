from pathlib import Path

from src.core.models import AlertConfig
from src.services.analyzer import OpportunityAnalyzer
from src.services.monitor import LocalMonitor
from src.storage.sqlite_repository import SQLiteRepository


class FakeClient:
    def __init__(self, html: str):
        self.html = html
        self.calls = []

    def fetch_search_page(self, **kwargs):
        self.calls.append(kwargs)
        return self.html if kwargs["page"] == 1 else ""


class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send(self, alert, listing, analysis):
        self.sent.append((alert, listing, analysis))


def test_monitor_scans_alert_with_location_range_and_dedupes(tmp_path, monkeypatch):
    monkeypatch.setattr("src.services.monitor.settings.MAX_SEARCH_PAGES", 2)
    monkeypatch.setattr("src.services.monitor.settings.DELAY_BETWEEN_PAGE_REQUESTS_SECONDS", 0)

    html = Path("tests/fixtures/search_next_data.html").read_text(encoding="utf-8")
    client = FakeClient(html)
    notifier = FakeNotifier()
    repository = SQLiteRepository(tmp_path / "monitor.sqlite3")
    monitor = LocalMonitor(
        client=client,
        analyzer=OpportunityAnalyzer(),
        repository=repository,
        notifier=notifier,
    )
    alert = AlertConfig(
        search_term="iphone 13",
        location="rio de janeiro",
        min_price_cents=150000,
        max_price_cents=250000,
        alert_id=1,
        chat_id="123",
    )

    first_result = monitor.scan_once(alert)
    second_result = monitor.scan_once(alert)

    assert first_result.fetched_count == 3
    assert first_result.notified_count == 1
    assert second_result.notified_count == 0
    assert len(notifier.sent) == 1
    assert client.calls[0]["location"] == "rio de janeiro"
    assert client.calls[0]["min_price"] == 1500
    assert client.calls[0]["max_price"] == 2500
